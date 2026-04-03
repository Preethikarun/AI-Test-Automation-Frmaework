from behave import given, when, then
from pages.todo_page import TodoPage


def get_todo(context):
    """Helper — get or create TodoPage instance."""
    if not hasattr(context, "todo"):
        context.todo = TodoPage(context.page)
    return context.todo


@given("the todo app is open")
def step_open_app(context):
    todo = get_todo(context)
    todo.navigate()


@when('I add a todo item "{text}"')
def step_add_item(context, text):
    get_todo(context).add_item(text)


@when("I complete todo item {index:d}")
def step_complete_item(context, index):
    get_todo(context).complete_item(index - 1)


@when("I delete todo item {index:d}")
def step_delete_item(context, index):
    get_todo(context).delete_item(index - 1)


@then("the todo count shows {count:d}")
def step_check_count(context, count):
    actual = get_todo(context).get_item_count()
    assert actual == count, (
        f"Expected count {count} but got {actual}"
    )

@then('the item "{text}" is visible')
def step_item_visible(context, text):
    assert get_todo(context).is_item_visible(text), (
        f"Item '{text}' not visible"
    )


@then('the item "{text}" is not visible')
def step_item_not_visible(context, text):
    assert not get_todo(context).is_item_visible(text), (
        f"Item '{text}' should not be visible"
    )