az login --service-principal -u "4a3ef9a6-ecef-41b1-bc12-bb4747e23d34" -p "XHI8Q~VsyOcet3oIIBw9yr1wxFvy5uXFPRz0paZi" --tenant "04bef963-8e9a-4766-96f0-8fe77f681932"


az group create `
  --name zava-rg `
  --location centralus

az postgres flexible-server create `
  --name $dbServerName `
  --resource-group zava-rg `
  --location centralus `
  --admin-user zavadmin `
  --admin-password $dbPassword `
  --sku-name Standard_B1ms `
  --tier Burstable `
  --version 15 `
  --storage-size 32 `
  --public-access All

az postgres flexible-server list -g zava-rg -o table

az appservice plan create `
  --name zava-plan `
  --resource-group zava-rg `
  --location centralus `
  --is-linux `
  --sku B1

$randomId = Get-Random -Minimum 1000 -Maximum 9999
$appName = "zava-backend-$randomId"
echo "App Service Name: $appName"


az webapp create `
  --name $appName `
  --resource-group zava-rg `
  --plan zava-plan `
  --runtime "PYTHON:3.11"

AZURE_SUBSCRIPTION_ID=<from Task 1>
AZURE_TENANT_ID=<from Task 1>
AZURE_CLIENT_ID=<from Task 2>
DB_SERVER_NAME=<$dbServerName from Task 4>
DB_PASSWORD=<$dbPassword from Task 4>
APP_SERVICE_NAME=<$appName from Task 6>