# Contact Fields

## Overview

Contact fields are persistent information about contacts who interact with your agents. By enabling contact fields in your tools, you elevate the user experience to a new level, as your agents can interact with the Weni Platform to accurately obtain information about the contact.

## How Contact Fields Work

When you mark a parameter as a contact field in your tool definition, that information becomes persistent in the user's profile within the Weni Platform. This creates several advantages:

1. **Improved User Experience**: Users don't need to repeatedly provide the same information in future interactions
2. **Personalized Interactions**: Agents can address users with personalized information from previous conversations
3. **Streamlined Conversations**: Reduces the number of questions agents need to ask, making interactions more efficient

## Implementing Contact Fields

To implement a contact field in your tool, you need to set the `contact_field` parameter to `true` in your agent definition YAML file:

```yaml
parameters:
  - tool_parameter:
      description: "User's full name"
      type: "string"
      required: true
      contact_field: true
```

When this parameter is processed during a conversation, the information provided by the user will be:

- [x] Stored in the Weni Platform associated with that specific contact
- [x] Available for retrieval and update in future interactions
- [x] Accessible to all agents that have permission to view this contact field

## Best Practices

When implementing contact fields, consider the following best practices:

- **Only store relevant information**: Not every parameter is necessarily a contact field; focus on information that will be useful in future interactions. Consider whether the parameter contains information important enough to be persisted for the contact.
- **Use descriptive parameter names**: This helps maintain organization when multiple contact fields are in use
- **Validate data before storing**: Ensure the information is in the correct format before saving it as a contact field

## Example Use Cases

Contact fields are particularly useful for:

- **Personal information**: Names, addresses, preferences
- **Account details**: Customer IDs, subscription types
- **Context-specific data**: Preferred language, communication preferences
- **Historical information**: Previous purchases, service history

By effectively utilizing contact fields, you can create more intelligent, context-aware agents that provide a seamless experience for your users.