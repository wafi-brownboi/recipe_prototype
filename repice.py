import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# DB config
db_config = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "recipe_db"  # <- Updated here
}

# --- Database Utilities ---
def get_connection():
    return mysql.connector.connect(**db_config)

# --- GUI Functions ---
def load_recipes():
    tree.delete(*tree.get_children())
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name, Skill_level FROM Recipe")
        for (rid, name, skill) in cursor.fetchall():
            tree.insert("", "end", iid=rid, values=(rid, name, skill))
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

def clear_form():
    entry_name.delete(0, tk.END)
    entry_serving.delete(0, tk.END)
    entry_prep.delete(0, tk.END)
    combo_skill.set("")
    text_instructions.delete("1.0", tk.END)
    text_notes.delete("1.0", tk.END)

def add_recipe():
    name = entry_name.get()
    serving = entry_serving.get()
    prep = entry_prep.get()
    skill = combo_skill.get()
    instructions = text_instructions.get("1.0", tk.END).strip()
    notes = text_notes.get("1.0", tk.END).strip()

    if not name:
        messagebox.showwarning("Validation", "Name is required.")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO Recipe (Name, Serving_quantity, Preparing_time, Skill_level, Instructions, Notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, serving, prep, skill, instructions, notes))
        conn.commit()
        messagebox.showinfo("Success", "Recipe added.")
        clear_form()
        load_recipes()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

def show_details(event):
    selected = tree.selection()
    if not selected:
        return
    rid = selected[0]
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Recipe WHERE ID = %s", (rid,))
        recipe = cursor.fetchone()
        if recipe:
            entry_name.delete(0, tk.END)
            entry_name.insert(0, recipe[1])
            text_instructions.delete("1.0", tk.END)
            text_instructions.insert(tk.END, recipe[2] or "")
            entry_serving.delete(0, tk.END)
            entry_serving.insert(0, recipe[3] or "")
            entry_prep.delete(0, tk.END)
            entry_prep.insert(0, recipe[4] or "")
            combo_skill.set(recipe[5] or "")
            text_notes.delete("1.0", tk.END)
            text_notes.insert(tk.END, recipe[6] or "")

            load_ingredients_for_recipe(rid)
    finally:
        conn.close()

def delete_recipe():
    selected = tree.selection()
    if not selected:
        return messagebox.showwarning("Delete", "Select a recipe to delete.")
    rid = selected[0]
    confirm = messagebox.askyesno("Confirm", "Are you sure to delete?")
    if not confirm:
        return
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Recipe WHERE ID = %s", (rid,))
        conn.commit()
        messagebox.showinfo("Deleted", "Recipe deleted.")
        clear_form()
        load_recipes()
        tree_ingredients.delete(*tree_ingredients.get_children())
    finally:
        conn.close()

def update_recipe():
    selected = tree.selection()
    if not selected:
        return messagebox.showwarning("Update", "Select a recipe to update.")
    rid = selected[0]

    name = entry_name.get()
    serving = entry_serving.get()
    prep = entry_prep.get()
    skill = combo_skill.get()
    instructions = text_instructions.get("1.0", tk.END).strip()
    notes = text_notes.get("1.0", tk.END).strip()

    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE Recipe SET Name=%s, Serving_quantity=%s, Preparing_time=%s, Skill_level=%s,
            Instructions=%s, Notes=%s WHERE ID=%s
        """
        cursor.execute(sql, (name, serving, prep, skill, instructions, notes, rid))
        conn.commit()
        messagebox.showinfo("Updated", "Recipe updated.")
        load_recipes()
    finally:
        conn.close()

def load_ingredients_for_recipe(recipe_id):
    tree_ingredients.delete(*tree_ingredients.get_children())
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.Name, ri.Quantity_used, ri.Unit
            FROM Recipe_Ingredients ri
            JOIN Ingredients i ON ri.Ingredient_ID = i.ID
            WHERE ri.Recipe_ID = %s
        """, (recipe_id,))
        for row in cursor.fetchall():
            tree_ingredients.insert("", "end", values=row)
    finally:
        conn.close()

# --- GUI Setup ---
root = tk.Tk()
root.title("Recipe Manager")
root.geometry("1000x650")

# Recipe Form
frame_form = tk.LabelFrame(root, text="Recipe Form", padx=10, pady=10)
frame_form.pack(padx=10, pady=10, fill="x")

tk.Label(frame_form, text="Name:").grid(row=0, column=0)
entry_name = tk.Entry(frame_form, width=40)
entry_name.grid(row=0, column=1)

tk.Label(frame_form, text="Serving:").grid(row=1, column=0)
entry_serving = tk.Entry(frame_form)
entry_serving.grid(row=1, column=1, sticky='w')

tk.Label(frame_form, text="Prep Time:").grid(row=2, column=0)
entry_prep = tk.Entry(frame_form)
entry_prep.grid(row=2, column=1, sticky='w')

tk.Label(frame_form, text="Skill:").grid(row=3, column=0)
combo_skill = ttk.Combobox(frame_form, values=["Easy", "Medium", "Hard"])
combo_skill.grid(row=3, column=1, sticky='w')

tk.Label(frame_form, text="Instructions:").grid(row=0, column=2)
text_instructions = tk.Text(frame_form, height=5, width=40)
text_instructions.grid(row=0, column=3, rowspan=2)

tk.Label(frame_form, text="Notes:").grid(row=2, column=2)
text_notes = tk.Text(frame_form, height=3, width=40)
text_notes.grid(row=2, column=3, rowspan=2)

tk.Button(frame_form, text="Add", command=add_recipe).grid(row=4, column=0)
tk.Button(frame_form, text="Update", command=update_recipe).grid(row=4, column=1)
tk.Button(frame_form, text="Delete", command=delete_recipe).grid(row=4, column=2)

# Recipe List
frame_list = tk.LabelFrame(root, text="Recipes")
frame_list.pack(padx=10, pady=5, fill="both", expand=True)

columns = ("ID", "Name", "Skill")
tree = ttk.Treeview(frame_list, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(fill="both", expand=True)
tree.bind("<<TreeviewSelect>>", show_details)

# Ingredients View
frame_ing = tk.LabelFrame(root, text="Ingredients Used in Recipe")
frame_ing.pack(padx=10, pady=5, fill="both", expand=True)

tree_ingredients = ttk.Treeview(frame_ing, columns=("Name", "Qty", "Unit"), show="headings")
for col in ("Name", "Qty", "Unit"):
    tree_ingredients.heading(col, text=col)
tree_ingredients.pack(fill="both", expand=True)

# Load data on start
load_recipes()
root.mainloop()
