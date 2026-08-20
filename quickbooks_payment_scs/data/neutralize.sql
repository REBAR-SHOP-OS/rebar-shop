-- disable QuickBooks payment provider
UPDATE payment_provider
   SET client_id=NULL, client_secret=NULL, auth_code=NULL, realm_id=NULL, access_token=NULL, refresh_token=NULL;
