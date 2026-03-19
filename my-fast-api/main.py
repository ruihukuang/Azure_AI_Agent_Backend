from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# This defines the "shape" of data your API expects
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/items/")
async def create_item(item: Item):
    return {"item_name": item.name, "item_price": item.price}


@app.get("/items/")  # Changed from .post to .get
async def read_items():
    # Since browsers can't send a "Body" easily, 
    # we just return some sample data for now.
    return [
        {"item_name": "Coffee", "item_price": 4.5},
        {"item_name": "Tea", "item_price": 3.0}
    ]