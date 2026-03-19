import logging
from azure.identity import DefaultAzureCredential
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from service.db_setup import SessionLocal
from service.model import ChatMessage
from config import Config
from service.schemas import ChatResponse # Import your schema

from sqlalchemy import func

# Get the logger configured in app.py
logger = logging.getLogger("semantic_kernel")

async def get_response(user_input, conversation_id, kernel, use_cache="none") -> ChatResponse:
    logger.info(f"🚀 Starting request for conversation {conversation_id}")
    db = SessionLocal()

    try:
        # 1. Search for existing record
        existing_record = db.query(ChatMessage).filter(
            ChatMessage.role == "user",
            ChatMessage.content == user_input
        ).order_by(ChatMessage.id.desc()).first()

        # ✅ ONLY log if the record actually exists
        if existing_record:
            logger.info(f"📅 Record found: {existing_record.id}")
            logger.info(f"🔍 Full Record Data: {existing_record.__dict__}")
        else:
            logger.info("🆕 No previous record found. This is a new question.")

        # 2. Case: Match found but user hasn't decided yet
        if existing_record and use_cache == "none":
            logger.info("📂 Cache hit: Previous answer found. Waiting for user confirmation.")
            return ChatResponse(
            status="needs_confirmation",
            content="", # No answer yet
            source="database",
            conversation_id=str(conversation_id),
            message="Previous answer found. Use it?" # <--- Using the optional field
    )


        # 3. Case: Match found and user wants the OLD answer
        if existing_record and use_cache == "true":
            logger.info("♻️ Cache use: Retrieving existing answer from database.")
            old_answer = db.query(ChatMessage).filter(
                ChatMessage.role == "assistant",
                ChatMessage.conversation_id == existing_record.conversation_id,
                ChatMessage.created_at >= existing_record.created_at,
                ChatMessage.id != existing_record.id
            ).order_by(ChatMessage.created_at.asc()).first() # Order by Time, not UUID like Id and could not compare id 
            return ChatResponse(
            status="success",
            content=old_answer.content if old_answer else "No answer found",
            source="database",
            conversation_id=str(conversation_id)
            )

            # ✅ ONLY log if the record actually exists
            if old_answer:
               logger.info(f"📅 Record relate to an old answer found: { old_answer.id}")
               logger.info(f"🔍 Full Record Data relate to an old answer: { old_answer.__dict__}")
            else:
               logger.info("🆕 No previous record for an old answer found.")

        # 4. Case: Proceed with RAG
        logger.info("🔍 RAG mode: Invoking RetrieverPlugin for context...")
        context_result = await kernel.invoke(plugin_name="RetrieverPlugin", function_name="get_context", query=user_input)
        context = str(context_result).strip()

        # --- ADDED LOG LINE ---
        logger.info(f"📄 Context Retrieved ({len(context)} chars): {context}...") 
        # ----------------------
        # For a new record
        if not existing_record:
            if not context or "No relevant incidents found" in context or context == "None":
                logger.warning("⚠️ RAG: No relevant context found. Falling back to system message.")
                response_text = "I'm sorry, I couldn't find any relevant incidents in the database to assist with this query."
                
                db.add(ChatMessage(conversation_id=conversation_id, role="user", content=user_input))
                db.flush()
                db.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=response_text))
                db.commit()
                return ChatResponse(
                status="success",
                content=response_text,
                source="system_fallback",
                conversation_id=str(conversation_id)
                )

        # LLM Completion
        logger.info("🧠 LLM: Sending prompt to Azure OpenAI...")
        history = ChatHistory()
        system_prompt = (
            "You are an expert AI assistant specializing in technical and business analysis. "
            "Your primary goal is to answer the user's question using ONLY the provided context from the database. "
            "\n\n--- GUIDELINES ---\n"
            "1. **Strict Grounding**: Do not use outside knowledge. If the answer isn't in the context, say 'I don't have enough information in the current knowledge base to answer that.'\n"
            "2. **Source Attribution**: When you find an answer, mention which source file it came from (e.g., 'According to Bizllm.md...').\n"
            "3. **Structure**: Use bullet points and clear headings for complex technical explanations.\n"
            "4. **Synthesis**: Since the context includes full file contents, look for connections across different parts of the document to provide a complete answer."
        )
        history.add_system_message(f"{system_prompt}\n\nContext: {context}")
        history.add_user_message(user_input)

        chat_completion = kernel.get_service(type=AzureChatCompletion)
        settings = AzureChatPromptExecutionSettings(
            service_id="default", 
            ai_model_id=Config.DEPLOYMENT_MODEL,
            temperature=Config.DEPLOYMENT_MODEL_TEMPERATURE,
            max_tokens=Config.DEPLOYMENT_MODEL_MAXTOKEN
        )
        
        response = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=settings 
        )
        response_text = str(response)
        logger.info("✨ LLM: Response generated successfully.")

        # Database updates
        # --- DATABASE UPDATE LOGIC ---
        if existing_record:
            # The User message already exists! Do NOT db.add(user_input) again.
            if use_cache == "false":
                logger.info("📝 Updating existing assistant record with fresh LLM response.")
                # Find the assistant message linked to this specific user entry
                old_assistant_msg = db.query(ChatMessage).filter(
                    ChatMessage.role == "assistant",
                    ChatMessage.conversation_id == existing_record.conversation_id,
                    ChatMessage.created_at >= existing_record.created_at,
                    ChatMessage.id != existing_record.id
                ).order_by(ChatMessage.created_at.asc()).first()

                # ✅ ONLY log if the record actually exists
                if  old_assistant_msg:
                    logger.info(f"📅 Record found for old_assistant_msg: {  old_assistant_msg.id}")
                    logger.info(f"🔍 Full Record Data for old_assistant_msg: {  old_assistant_msg.__dict__}")
                else:
                    logger.info("🆕 No previous record for  old_assistant_msg found.")
                
                if old_assistant_msg:
                    old_assistant_msg.content = response_text
                else:
                    # User existed but Assistant didn't (maybe a previous crash)
                    db.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=response_text))
            else:
                # use_cache was "true" or "none" but we generated a response anyway (fallback)
                db.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=response_text))
        
        else:
            # 💾 BRAND NEW: Neither User nor Assistant exists
            logger.info("💾 Saving brand new interaction to database.")
            db.add(ChatMessage(conversation_id=conversation_id, role="user", content=user_input))
            db.flush() 
            db.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=response_text))
        
        db.commit()
        return ChatResponse(
        status="success",
        content=response_text,
        source="llm",
        conversation_id=str(conversation_id)
    )

    except Exception as e:
        logger.error(f"❌ Orchestrator Error: {str(e)}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()