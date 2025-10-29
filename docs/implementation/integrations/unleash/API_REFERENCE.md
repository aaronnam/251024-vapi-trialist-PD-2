# Unleash API Documentation Reference

Captured from https://help.unleash.so/apidocs on 2025-10-27

## Overview

Unleash provides a permission-aware, personalized API for searching across unstructured data in organizations. The API enables creation of dynamic, knowledge-driven workflows including:
- Tailored search assistants or chatbots
- Embedded search in knowledge bases or support portals
- White-labeled integrated search experiences

## Base Configuration

- **Base URL:** `https://e-api.unleash.so/`
- **For Private Tenants:** `https://app.{tenant}.unleash.so/e-api/`
- **Swagger Documentation:** https://api.unleash.wiki

## Authentication

### API Key Creation
1. Go to Admin Center > API Keys
2. Create API Key with name
3. Select access mode and scope
4. Copy and securely store the key (cannot be viewed again)

### Access Modes
- **Non-Impersonated:** API requests executed on behalf of the key creator (regular users)
- **Impersonated:** Requires `unleash-account` header to specify user identity (admin only)

### Headers
- `Authorization: Bearer {api_key}` (required)
- `unleash-account: {email_or_account_id}` (optional, for impersonated keys)
- `Content-Type: application/json`

### Scope
API keys should be restricted to specific assistants. Platform-wide access is not recommended.

## Search Endpoint

### POST /search

Search for resources using a query and filters.

#### Request Body
```json
{
  "query": "search term",
  "assistantId": "optional_assistant_id",
  "contentSearch": true,
  "semanticSearch": true,
  "filters": {
    "type": ["array", "of", "types"],
    "isStarred": true/false,
    "hasAttachments": true/false,
    "appId": ["array_of_app_ids"],
    "label": ["array_of_labels"],
    "status": ["array_of_statuses"],
    "fromTime": "ISO_date_string",
    "untilTime": "ISO_date_string",
    "createBeforeTime": "ISO_date_string",
    "createAfterTime": "ISO_date_string"
  },
  "sort": {
    // sorting configuration
  },
  "paging": {
    "pageSize": 10,
    "pageNumber": 0
  }
}
```

#### Response (200 OK)
```json
{
  "totalResults": 42,
  "results": [
    {
      "resource": {
        "title": "Resource Title",
        "description": "Resource description",
        // additional resource fields
      },
      "snippet": "Relevant text snippet from the resource",
      "highlights": ["array", "of", "highlighted", "terms"]
    }
  ],
  "paging": {
    // paging information
  },
  "requestId": "unique_request_id_for_debugging"
}
```

#### Error Responses
- **400 Bad Request:** Invalid query or parameters
- **401 Unauthorized:** Invalid or missing API key
- **500+ Server Error:** Temporary service issues

## Other Modules

### Chat
- Module for conversational interactions
- Endpoint details available in full API documentation

### Filters
- Pre-defined filter management
- Statistical analysis of filter usage

### Tokens
- Custom user token generation
- Session management

### Resources
- Direct resource access and management

## Error Handling

All endpoints return a `RequestId` in both response body and header for debugging. API errors follow RFC 7807 standardized REST error format.

## Rate Limiting

Not explicitly documented, but standard practices apply. Monitor for 429 responses.

## Support

Contact: support@unleash.so

## Postman Collection

Available at: unleash.postman_collection.json (downloadable from documentation site)