# main.py

import os
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from dotenv import load_dotenv
import requests
import pandas as pd
from pdf_test import generate_pdf  # Ensure this module is available

# Optional: Set window size (useful during development)
# Window.size = (360, 640)

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")
LOGO_PATH = os.getenv("LOGO_PATH")
PASSWORD = os.getenv("PASSWORD")


class LoginScreen(Screen):
    def do_login(self):
        password_input = self.ids.password_input.text
        if password_input == PASSWORD:
            self.manager.current = 'main'
            self.ids.password_input.text = ''
            self.ids.message.text = ''
        else:
            self.ids.message.text = 'Incorrect password'


class MainScreen(Screen):
    pass


class CategoriesScreen(Screen):
    categories = ListProperty([])

    def on_pre_enter(self):
        self.fetch_categories()

    def fetch_categories(self):
        try:
            response = requests.get(f"{API_URL}/categories/")
            if response.status_code == 200:
                self.categories = response.json()
                self.display_categories()
            else:
                self.show_dialog("Error", "Failed to fetch categories")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch categories: {e}")

    @mainthread
    def display_categories(self):
        categories_list = self.ids.categories_list
        categories_list.clear_widgets()
        for category in self.categories:
            item = OneLineListItem(text=f"ID: {category['id']} | Name: {category['name']}")
            categories_list.add_widget(item)

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class ItemsScreen(Screen):
    items = ListProperty([])

    def on_pre_enter(self):
        self.fetch_items()

    def fetch_items(self):
        try:
            response = requests.get(f"{API_URL}/items/")
            if response.status_code == 200:
                self.items = response.json()
                self.display_items()
            else:
                self.show_dialog("Error", "Failed to fetch items")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch items: {e}")

    @mainthread
    def display_items(self):
        items_list = self.ids.items_list
        items_list.clear_widgets()
        for item in self.items:
            text = f"ID: {item['id']} | Name: {item['name']} | Qty: {item['quantity']}"
            list_item = OneLineListItem(text=text)
            items_list.add_widget(list_item)

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class CreateCategoryScreen(Screen):
    def create_category(self):
        name = self.ids.category_name.text.strip()
        description = self.ids.category_description.text.strip()

        if not name:
            self.show_dialog("Error", "Category name cannot be empty")
            return

        try:
            response = requests.post(f"{API_URL}/categories/", json={"name": name, "description": description})
            if response.status_code == 201:
                self.show_dialog("Success", "Category created successfully")
                self.ids.category_name.text = ''
                self.ids.category_description.text = ''
            else:
                self.show_dialog("Error", f"Failed to create category: {response.text}")
        except Exception as e:
            self.show_dialog("Error", f"Failed to create category: {e}")

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class EditCategoryScreen(Screen):
    category_names = ListProperty([])
    selected_category = StringProperty('')
    selected_category_id = NumericProperty(None)

    def on_pre_enter(self):
        self.fetch_categories()

    def fetch_categories(self):
        try:
            response = requests.get(f"{API_URL}/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.category_names = [cat['name'] for cat in categories]
                self.categories = categories
            else:
                self.show_dialog("Error", "Failed to fetch categories")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch categories: {e}")

    def on_category_select(self, selected_name):
        category = next((cat for cat in self.categories if cat['name'] == selected_name), None)
        if category:
            self.selected_category_id = category['id']
            self.ids.new_category_name.text = category['name'] or ''
            self.ids.new_category_description.text = category.get('description', '') or ''

    def update_category(self):
        new_name = self.ids.new_category_name.text.strip()
        new_description = self.ids.new_category_description.text.strip()

        if not new_name:
            self.show_dialog("Error", "Category name cannot be empty")
            return

        if not self.selected_category_id:
            self.show_dialog("Error", "No category selected")
            return

        try:
            response = requests.put(
                f"{API_URL}/categories/{self.selected_category_id}/",
                json={
                    "name": new_name,
                    "description": new_description
                }
            )
            if response.status_code == 200:
                self.show_dialog("Success", "Category updated successfully")
                self.ids.new_category_name.text = ''
                self.ids.new_category_description.text = ''
                self.manager.current = 'categories'
            else:
                self.show_dialog("Error", f"Failed to update category: {response.text}")
        except requests.exceptions.RequestException as e:
            self.show_dialog("Error", f"Failed to update category: {e}")

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class DeleteCategoryScreen(Screen):
    category_names = ListProperty([])
    selected_category = StringProperty('')
    selected_category_id = NumericProperty(None)

    def on_pre_enter(self):
        self.fetch_categories()

    def fetch_categories(self):
        try:
            response = requests.get(f"{API_URL}/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.category_names = [cat['name'] for cat in categories]
                self.categories = categories
            else:
                self.show_dialog("Error", "Failed to fetch categories")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch categories: {e}")

    def on_category_select(self, selected_name):
        category = next((cat for cat in self.categories if cat['name'] == selected_name), None)
        if category:
            self.selected_category = category['name']
            self.selected_category_id = category['id']

    def delete_category(self):
        confirmation_text = self.ids.confirmation_input.text.strip().lower()
        expected_text = f"delete {self.selected_category.lower()}"

        if confirmation_text != expected_text:
            self.show_dialog("Error", f'Please type "delete {self.selected_category}" to confirm.')
            return

        if not self.selected_category_id:
            self.show_dialog("Error", "No category selected")
            return

        def confirm_deletion():
            try:
                response = requests.delete(f"{API_URL}/categories/{self.selected_category_id}/")
                if response.status_code == 204:
                    self.show_dialog("Success", "Category deleted successfully")
                    self.ids.confirmation_input.text = ''
                    self.manager.current = 'categories'
                else:
                    self.show_dialog("Error", f"Failed to delete category: {response.text}")
            except Exception as e:
                self.show_dialog("Error", f"Failed to delete category: {e}")

        # Confirmation dialog
        confirmation_dialog = MDDialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete category '{self.selected_category}'?",
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="Yes",
                    on_release=lambda x: [confirm_deletion(), confirmation_dialog.dismiss()]
                ),
                MDRaisedButton(
                    text="No",
                    on_release=lambda x: confirmation_dialog.dismiss()
                )
            ]
        )
        confirmation_dialog.open()

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class CreateItemScreen(Screen):
    category_names = ListProperty([])
    category_dict = {}

    def on_pre_enter(self):
        self.fetch_categories()

    def fetch_categories(self):
        try:
            response = requests.get(f"{API_URL}/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.category_names = [cat['name'] for cat in categories]
                self.category_dict = {cat['name']: cat['id'] for cat in categories}
            else:
                self.show_dialog("Error", "Failed to fetch categories")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch categories: {e}")

    def create_item(self):
        name = self.ids.item_name.text.strip()
        description = self.ids.item_description.text.strip()
        quantity = self.ids.item_quantity.text.strip()
        category_name = self.ids.item_category_spinner.text

        if not name:
            self.show_dialog("Error", "Item name cannot be empty")
            return

        if not quantity.isdigit() or int(quantity) < 1:
            self.show_dialog("Error", "Quantity must be a positive integer")
            return

        if category_name not in self.category_dict:
            self.show_dialog("Error", "Please select a valid category")
            return

        category_id = self.category_dict[category_name]

        try:
            response = requests.post(f"{API_URL}/items/", json={
                "name": name,
                "description": description,
                "quantity": int(quantity),
                "category_id": category_id
            })
            if response.status_code == 201:
                self.show_dialog("Success", "Item created successfully")
                self.ids.item_name.text = ''
                self.ids.item_description.text = ''
                self.ids.item_quantity.text = ''
                self.ids.item_category_spinner.text = 'Select Category'
            else:
                self.show_dialog("Error", f"Failed to create item: {response.text}")
        except Exception as e:
            self.show_dialog("Error", f"Failed to create item: {e}")

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class EditItemScreen(Screen):
    category_names = ListProperty([])
    category_dict = {}
    current_item_id = NumericProperty(None)

    def on_pre_enter(self):
        self.fetch_categories()

    def fetch_categories(self):
        try:
            response = requests.get(f"{API_URL}/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.category_names = [cat['name'] for cat in categories]
                self.category_dict = {cat['name']: cat['id'] for cat in categories}
            else:
                self.show_dialog("Error", "Failed to fetch categories")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch categories: {e}")

    def load_item(self):
        item_id = self.ids.edit_item_id.text.strip()
        if not item_id.isdigit():
            self.show_dialog("Error", "Invalid Item ID")
            return

        try:
            response = requests.get(f"{API_URL}/items/{item_id}/")
            if response.status_code == 200:
                item = response.json()
                self.current_item_id = item['id']
                self.ids.edit_item_name.text = item['name'] or ''
                self.ids.edit_item_description.text = item.get('description', '') or ''
                self.ids.edit_item_quantity.text = str(item.get('quantity', '')) or ''
                category_name = next((name for name, cid in self.category_dict.items() if cid == item['category_id']), 'Select Category')
                self.ids.edit_item_category_spinner.text = category_name
            else:
                self.show_dialog("Error", f"Item not found: {response.text}")
        except Exception as e:
            self.show_dialog("Error", f"Failed to fetch item details: {e}")

    def update_item(self):
        if not self.current_item_id:
            self.show_dialog("Error", "No item loaded to update")
            return

        name = self.ids.edit_item_name.text.strip()
        description = self.ids.edit_item_description.text.strip()
        quantity = self.ids.edit_item_quantity.text.strip()
        category_name = self.ids.edit_item_category_spinner.text

        if not name:
            self.show_dialog("Error", "Item name cannot be empty")
            return

        if not quantity.isdigit() or int(quantity) < 1:
            self.show_dialog("Error", "Quantity must be a positive integer")
            return

        if category_name not in self.category_dict:
            self.show_dialog("Error", "Please select a valid category")
            return

        category_id = self.category_dict[category_name]

        try:
            response = requests.put(f"{API_URL}/items/{self.current_item_id}/", json={
                "name": name,
                "description": description,
                "quantity": int(quantity),
                "category_id": category_id
            })
            if response.status_code == 200:
                self.show_dialog("Success", "Item updated successfully")
                self.ids.edit_item_id.text = ''
                self.ids.edit_item_name.text = ''
                self.ids.edit_item_description.text = ''
                self.ids.edit_item_quantity.text = ''
                self.ids.edit_item_category_spinner.text = 'Select Category'
                self.current_item_id = None
            else:
                self.show_dialog("Error", f"Failed to update item: {response.text}")
        except Exception as e:
            self.show_dialog("Error", f"Failed to update item: {e}")

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class DeleteItemScreen(Screen):
    def delete_item(self):
        item_id = self.ids.delete_item_id.text.strip()
        if not item_id.isdigit():
            self.show_dialog("Error", "Invalid Item ID")
            return

        def confirm_deletion():
            try:
                response = requests.delete(f"{API_URL}/items/{item_id}/")
                if response.status_code == 204:
                    self.show_dialog("Success", "Item deleted successfully")
                    self.ids.delete_item_id.text = ''
                else:
                    self.show_dialog("Error", f"Failed to delete item: {response.text}")
            except Exception as e:
                self.show_dialog("Error", f"Failed to delete item: {e}")

        # Confirmation dialog
        confirmation_dialog = MDDialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete item ID '{item_id}'?",
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="Yes",
                    on_release=lambda x: [confirm_deletion(), confirmation_dialog.dismiss()]
                ),
                MDRaisedButton(
                    text="No",
                    on_release=lambda x: confirmation_dialog.dismiss()
                )
            ]
        )
        confirmation_dialog.open()

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, None),
            height=dp(200),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class InventoryApp(MDApp):
    def build(self):
        self.title = "Inventory Management System"
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.theme_style = "Light"
        return Builder.load_file('inventory.kv')


if __name__ == '__main__':
    InventoryApp().run()
