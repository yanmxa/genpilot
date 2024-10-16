
## Response

Your response must be a JSON object containing the following fields:

    1. thought: Represents your internal thought process regarding the current task. This field is used to plan the solution and outline the next steps.

    2. action: Describes the tool needed to gather knowledge or perform actions.

       2.1 name: The tool name used for the action.

       2.2 args: The arguments passed to the tool.
       
    3. answer: At the end of the task, include this field with the final answer or response to the initial question or task.

Note: Your response should include either the thought and action fields, or the answer field — but not both at the same time.

### Response example

~~~json
{
    "thought": [
        "The user has requested extracting a zip file downloaded yesterday.",
        "Steps to solution are...",
        "I will process step by step...",
        "Analysis of step..."
    ],
    "action": {
      "name": "tool_name",
      "args": {"arg1": "val1", "arg2": "val2", "arg3": "val3"},
    },
    "answer": "the zip file is ..."
}
~~~
