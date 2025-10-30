## Voice Agent to Salesforce Integration Process

**Overview:** After each voice agent call, create a Salesforce event record to track the engagement on the contact/lead's activity stream.

### Data Collection
1. Voice agent call completes
2. Collect call data including:
   - Business email address (from pre-call form)
   - Call timestamp
   - Call summary/description
   - Any other relevant call metadata

### Data Storage
3. Store call data in S3 bucket (AWS)

### Scheduled Processing (Daily Cron Job)
4. Run daily cron job that:

   **Step 1: Retrieve call data**
   - Pull new call records from S3 bucket

   **Step 2: Query Salesforce for contact/lead**
   - Use Salesforce API to query for Lead or Contact by email address
   - Query both Lead and Contact objects (trialists could be either)
   - Retrieve the record ID

   **Step 3: Determine assignment**
   - If Lead/Contact has an owner → use that owner ID
   - If no owner → assign to admin account

   **Step 4: Create Salesforce Event**
   - Use Salesforce API to create Event record with:
     - **who_id**: Lead/Contact ID from Step 2
     - **Type**: "Voice AI Call"
     - **OwnerId** (Assigned To): Owner ID or admin account from Step 3
     - **Subject**: "Voice AI Call [date]"
     - **StartDateTime**: Call timestamp
     - **Description**: Call summary

### Testing
5. Test full integration in Salesforce full data sandbox before production deployment

### API Requirements
- Salesforce API access (already provisioned for Aaron's account)
- Ability to execute SOQL queries (for lead/contact lookup)
- Ability to create Event records via REST/SOAP API