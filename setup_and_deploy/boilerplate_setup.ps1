$project_id = "some-google-project-id"  # change this
$billing_account = "1A2B3C-1A2B3C-1A2B3C"  # change this
$default_location = "us-central1"  # change this
$function_name = "receiver"  # don't change this
$trigger_url = "https://${default_location}-${project_id}.cloudfunctions.net/${function_name}"  # change this
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
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable calendar-json.googleapis.com

# give yourself a service account so you can run this app locally
gcloud iam service-accounts create telegram-service-account
gcloud projects add-iam-policy-binding ${project_id} --member="serviceAccount:telegram-service-account@${project_id}.iam.gserviceaccount.com" --role="roles/owner"
gcloud iam service-accounts keys create telegram-service-account.json --iam-account=telegram-service-account@${project_id}.iam.gserviceaccount.com

# link your local projects with the service account during runtime
$cwd = (Get-Item .).FullName
[System.Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "${cwd}\telegram-service-account.json", [System.EnvironmentVariableTarget]::Machine)

# setup bigquery
bq mk ${bigquery_dataset}

# setup the cron job
gcloud scheduler jobs create http telegramjob --schedule "0 6,16,20 * * *" --uri ${trigger_url} --http-method GET --time-zone "Africa/Johannesburg"
# y
# 14

# now you can run deploy.ps1


