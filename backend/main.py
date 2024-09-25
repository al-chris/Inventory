# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from database import engine, SessionLocal, Item, Category, Log, Base
from util import dict_to_text_description
from datetime import datetime

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# # Function to run migrations
# def run_migrations():
#     alembic_cfg = Config("alembic.ini")
#     command.upgrade(alembic_cfg, "head")

# # Startup event to run migrations
# @app.on_event("startup")
# async def startup_event():
#     run_migrations()

# Function to create a log entry
def create_log(action, item_id=None, category_id=None, quantity_change=None, description=None, db=None):
    log_entry = Log(
        action=action,
        item_id=item_id,
        category_id=category_id,
        quantity_change=quantity_change,
        description=description
    )
    db.add(log_entry)
    db.commit()


@app.post("/categories/")
def create_category(name: str, db: Session = Depends(get_db)):
    try:
        db_category = Category(name=name)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        # Log the category creation
        msg = f"Created Category: {name}"
        create_log(
            action="create_category", 
            category_id=db_category.id, 
            description=msg,
            db=db
        )

        return db_category
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating category")

@app.get("/categories/")
def read_categories(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        categories = db.query(Category).offset(skip).limit(limit).all()
        return categories
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/categories/{category_id}")
def read_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# update category name
@app.put("/categories/{category_id}")
def update_category(category_id: int, name: str, description: str, db: Session = Depends(get_db)):
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        changes = {}
        old_name = category.name
        
        if name is not None and name != old_name:
            changes["category_name"] = {"old": old_name, "new": name}
            category.name = name
        
        if description is not None and description != category.description:
            changes["description"] = {"old": category.description, "new": description}
            category.description = description
        
        db.commit()
        db.refresh(category)

        # Log the category update
        create_log(
            action="update_category", 
            category_id=category.id, 
            description=dict_to_text_description(changes),
            db=db
        )

        return category
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error updating category")

# DELETE a category
@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    print("attempting to delete category")
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Log the category deletion
    msg = f"Deleted Category: {db_category.name}"
    create_log(
        action="delete_category",
        category_id=category_id,
        description=msg,
        db=db
    )
    
    # Delete the category
    db.delete(db_category)
    db.commit()
    
    return {"message": "Category deleted"}

@app.post("/items/")
def create_item(name: str, description: str, category_id: int, quantity: int, db: Session = Depends(get_db)):
    try:
        db_item = Item(name=name, description=description, category_id=category_id, quantity=quantity)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        # Log the item creation
        msg = f"Created Item: {name}, Quantity: {quantity}"
        create_log(
            action="create_item", 
            item_id=db_item.id, 
            category_id=category_id, 
            description=msg, 
            db=db
        )

        return db_item
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating item")


@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    name: str = None,
    description: str = None,
    quantity: int = None,
    category_id: int = None,
    db: Session = Depends(get_db)
):
    # Fetch the item to be updated
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Variables to track changes for logging
    changes = {}
    quantity_change = None

    # Update the fields if new values are provided and log changes
    if name is not None and name != item.name:
        changes['name'] = {'old': item.name, 'new': name}
        item.name = name
    if description is not None and description != item.description:
        changes['description'] = {'old': item.description, 'new': description}
        item.description = description
    if quantity is not None and quantity != item.quantity:
        quantity_change = quantity - item.quantity  # Log the quantity change
        changes['quantity'] = {'old': item.quantity, 'new': quantity}
        item.quantity = quantity
    if category_id is not None and category_id != item.category_id:
        # Ensure category exists
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        changes['category_id'] = {'old': item.category_id, 'new': category_id}
        item.category_id = category_id

    # Commit the updates to the database
    try:
        db.commit()
        db.refresh(item)
        
        # Log changes if any fields were updated
        if changes:
            create_log(
                action="update_item", 
                item_id=item.id, 
                category_id=item.category_id, 
                quantity_change=quantity_change,
                description=dict_to_text_description(changes), 
                db=db
            )
            print("Log Created")
            print(changes)
        
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error updating item")

    return item

# DELETE an item
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    category_id = db_item.category_id
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Log the item deletion
    msg = f"Deleted Item: {db_item.name}"
    create_log(
        action="delete_item",
        item_id=item_id,
        category_id=category_id,
        description=msg,
        db=db
    )
    
    # Delete the item
    db.delete(db_item)
    db.commit()
    
    return {"message": "Item deleted"}

@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "quantity": item.quantity,
        "category_id": item.category_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }


@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.get("/search/")
def search_items(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    try:
        items = db.query(Item).filter(
            Item.name.contains(query) | Item.description.contains(query)
        ).all()
        if not items:
            raise HTTPException(status_code=404, detail="No items found")
        return items
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/categories/{category_id}/items/")
def read_items_by_category(category_id: int, db: Session = Depends(get_db)):
    items = db.query(Item).filter(Item.category_id == category_id).all()
    if not items:
        raise HTTPException(status_code=404, detail="No items found for this category")
    return items


@app.get("/categories/{category_id}/logs/")
def get_logs_by_category(category_id: int, db: Session = Depends(get_db)):
    try:
        logs = db.query(Log).filter(Log.category_id == category_id).all()
        if not logs:
            raise HTTPException(status_code=404, detail="No logs found for this category.")
        return logs
    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail="Error fetching logs for the category")

# Fetch logs, including those of deleted categories
@app.get("/logs/deleted_categories")
def read_logs_of_deleted_categories(db: Session = Depends(get_db)):
    try:
        logs_of_deleted_categories = db.query(Log).filter(Log.action == "delete_category").all()
        return logs_of_deleted_categories
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch logs of deleted categories")