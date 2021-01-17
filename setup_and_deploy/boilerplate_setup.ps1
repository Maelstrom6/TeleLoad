$project_id = "some-google-project-id"  # change this
$billing_account = "1A2B3C-1A2B3C-1A2B3C"  # change this
$function_name = "receiver"  # change this
$trigger_url = "https://location-${project_id}.cloudfunctions.net/${function_name}"  # change this
$bigquery_dataset = "telegramdataset"  # change this

# install the gcloud sdk and log in
gcloud projects create ${project_id}
gcloud config set project ${project_id}

# go to the gcloud website and go to billing to find your billing account ID
gcloud components install alpha
gcloud components install beta
gcloud beta billing projects link ${project_id} --billing-account ${billing_account}

# enable the APIs that we will use
# takes a few minutes to propage accross the network
gcloud services enable cloudbuild.googleapis.com
gcloud services enable appengine.googleapis.com
Start-Sleep 120


# give yourself a service account so you can run this app locally
gcloud iam service-accounts create telegram-service-account
gcloud projects add-iam-policy-binding ${project_id} --member="serviceAccount:telegram-service-account@${project_id}.iam.gserviceaccount.com" --role="roles/owner"
gcloud iam service-accounts keys create telegram-service-account.json --iam-account=telegram-service-account@${project_id}.iam.gserviceaccount.com

# link your local projects with the service account during runtime
$cwd = (Get-Item .).FullName
Set-Variable GOOGLE_APPLICATION_CREDENTIALS="${cwd}\telegram-service-account.json"



# setup bigquery
bq mk ${bigquery_dataset}

# setup the cron job
gcloud scheduler jobs create http telegramjob --schedule "0 6,16,20 * * *" --uri ${trigger_url} --http-method GET --time-zone "Africa/Johannesburg"

# now you can run deploy.ps1


