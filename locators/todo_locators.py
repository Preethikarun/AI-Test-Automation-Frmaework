"""
This is a dict — key-value pairs in curly braces. 
Page class uses these keys, never the raw selectors directly — so if a selector changes, you update it here once.
"""

TODO_LOCATORS = {
    "new_input":       "input.new-todo",
    "todo_items":      ".todo-list li",
    "item_label":      ".todo-list li label",
    "item_checkbox":   ".todo-list li .toggle",
    "todo_count":      ".todo-count strong",
    "clear_completed": "button.clear-completed",
    "toggle_all":      "label[for='toggle-all']",
    "filter_all":      "a[href='#/']",
    "filter_active":   "a[href='#/active']",
    "filter_completed":"a[href='#/completed']",
}
