import os
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000"

st.title("Inventory Management System")

# User Authentication (Simple Password Protection)
password = st.sidebar.text_input("Enter Password", type="password")
if password != os.getenv("PASSWORD"):
    st.warning("Incorrect password")
    st.stop()

# Display Categories
st.header("Categories")
try:
    categories = requests.get(f"{API_URL}/categories/").json()
    category_dict = {category['id']: category['name'] for category in categories}

    if categories:
        selected_category = st.selectbox("Select Category", options=[name for name in category_dict.values()])
        selected_category_id = next((id for id, name in category_dict.items() if name == selected_category), None)

        if st.button(f"Show Items in {selected_category}"):
            if selected_category_id:
                items = requests.get(f"{API_URL}/categories/{selected_category_id}/items/").json()
                if items:
                    st.subheader(f"Items in {selected_category}")
                    st.table(items)

                    # Convert items to a DataFrame for download
                    items_df = pd.DataFrame(items)
                    csv_data = items_df.to_csv(index=False)

                    # Add download button
                    st.download_button(
                        label="Download items as CSV",
                        data=csv_data,
                        file_name=f"{selected_category}_items.csv",
                        mime='text/csv'
                    )
                else:
                    st.info(f"No items found in {selected_category}")
            else:
                st.error("Selected category ID not found.")
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching categories: {e}")

# Create Category
st.header("Create New Category")
new_category_name = st.text_input("Category Name")
if st.button("Create Category"):
    try:
        response = requests.post(f"{API_URL}/categories/", params={"name": new_category_name})
        response.raise_for_status()
        st.success("Category created successfully")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to create category: {e}")

# Edit Category
st.header("Edit Category Name")
with st.expander("Click to Edit a category name"):
    try:
        if categories:
            category_to_edit = st.selectbox("Select Category to Edit", options=[name for name in category_dict.values()])
            category_id_to_edit = next((id for id, name in category_dict.items() if name == category_to_edit), None)
            new_category_name = st.text_input("New Category Name", value=category_to_edit)

            if st.button("Update Category Name"):
                if category_id_to_edit:
                    try:
                        response = requests.put(f"{API_URL}/categories/{category_id_to_edit}", params={"name": new_category_name})
                        response.raise_for_status()
                        st.success(f"Category name updated to '{new_category_name}' successfully")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to update category name: {e}")
                else:
                    st.error("Selected category ID not found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching categories: {e}")

# Display Items
st.header("Items")
try:
    items = requests.get(f"{API_URL}/items/").json()
    with st.expander("Click to Show All Items"):
        # st.write("This is the content inside the expander.")
        st.write(items)
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching items: {e}")

# Create Item
st.header("Create New Item")
with st.expander("Click to Create a New Item"):
    item_name = st.text_input("Item Name")
    item_description = st.text_area("Item Description")
    item_quantity = st.number_input("Quantity", min_value=0, step=1)

    # Check if there are categories available
    if categories:
        category_name = st.selectbox("Category", [category['name'] for category in categories])
        category_id = next((id for id, name in category_dict.items() if name == category_name), None)
    else:
        category_id = None

    # Button to create a new item
    if st.button("Create Item"):
        if category_id is None:
            st.error("Please create a category first.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/items/",
                    params={
                        "name": item_name,
                        "description": item_description,
                        "category_id": category_id,
                        "quantity": item_quantity
                    }
                )
                response.raise_for_status()
                st.success("Item created successfully")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to create item: {e}")

# Edit Item
st.header("Edit Item")
with st.expander("Click to Edit an Item"):
    item_id_to_edit = st.number_input("Enter Item ID to Edit", min_value=1, step=1)
    if item_id_to_edit:
        try:
            item = requests.get(f"{API_URL}/items/{item_id_to_edit}").json()
            if all(key in item for key in ['name', 'description', 'quantity', 'category_id']):
                item_name_edit = st.text_input("Edit Item Name", value=item['name'])
                item_description_edit = st.text_area("Edit Item Description", value=item['description'])
                item_quantity_edit = st.number_input("Edit Quantity", value=item['quantity'], min_value=0, step=1)
                item_category_name_edit = st.selectbox(
                    "Edit Category",
                    [category['name'] for category in categories],
                    index=next((i for i, cat in enumerate(categories) if cat['id'] == item['category_id']), 0)
                )
                category_id_edit = next((id for id, name in category_dict.items() if name == item_category_name_edit), None)

                if st.button("Update Item"):
                    if category_id_edit is not None:
                        try:
                            response = requests.put(
                                f"{API_URL}/items/{item_id_to_edit}",
                                params={
                                    "name": item_name_edit,
                                    "description": item_description_edit,
                                    "quantity": item_quantity_edit,
                                    "category_id": category_id_edit
                                }
                            )
                            response.raise_for_status()
                            st.success("Item updated successfully")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to update item: {e}")
                    else:
                        st.error("Selected category ID not found.")
            else:
                st.error("Item response missing expected fields.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching item details: {e}")

# Search Items
st.header("Search Items")
search_query = st.text_input("Enter search query")
if st.button("Search"):
    try:
        response = requests.get(f"{API_URL}/search/", params={"query": search_query})
        response.raise_for_status()
        search_results = response.json()
        if search_results:
            st.write("Search Results:")
            st.table(search_results)

            # Convert search results to a DataFrame for download
            search_results_df = pd.DataFrame(search_results)
            csv_data = search_results_df.to_csv(index=False)

            # Add download button
            st.download_button(
                label="Download search results as CSV",
                data=csv_data,
                file_name="search_results.csv",
                mime='text/csv'
            )
        else:
            st.info("No items found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching for items: {e}")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")



# Function to fetch categories
def fetch_categories():
    try:
        response = requests.get(f"{API_URL}/categories/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch categories: {e}")
        return []

# Function to fetch logs by category
def fetch_logs_by_category(category_id):
    try:
        response = requests.get(f"{API_URL}/categories/{category_id}/logs/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch logs: {e}")
        return []

# View Logs Section
st.header("View Logs by Category")

# Fetch categories and display a dropdown for selection
categories = fetch_categories()

# Debugging: Check if categories were fetched correctly
# st.write("Fetched Categories:", categories)

if categories:
    # Creating a dictionary to map category names to their IDs
    category_options = {category['name']: category['id'] for category in categories}
    
    # Debugging: Display the category options available
    # st.write("Category Options:", category_options)

    # Dropdown to select a category
    selected_category = st.selectbox("Select a category", list(category_options.keys()))

    if selected_category:
        # Get the selected category's ID
        category_id = category_options[selected_category]

        # Debugging: Display the selected category and its ID
        # st.write(f"Selected Category: {selected_category} (ID: {category_id})")

        # Button to view logs for the selected category
        if st.button("View Logs"):
            # Fetch logs for the selected category
            logs = fetch_logs_by_category(category_id)

            # Debugging: Display the fetched logs
            # st.write("Fetched Logs:", logs)

            if logs:
                # Convert logs to DataFrame for display and download
                logs_df = pd.DataFrame(logs)
                st.write("Logs for selected category:")
                st.table(logs_df)

                # Button to download the logs as a CSV file
                csv_data = logs_df.to_csv(index=False)
                st.download_button(
                    label="Download logs as CSV",
                    data=csv_data,
                    file_name=f"{selected_category}_logs.csv",
                    mime='text/csv'
                )
            else:
                st.info("No logs found for this category.")
else:
    st.info("No categories found.")