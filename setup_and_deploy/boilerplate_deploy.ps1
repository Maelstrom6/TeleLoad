$project_id = "some-google-project-id"  # change this
$default_location = "us-central1"  # change this
$function_name = "receiver"  # don't change this
$trigger_url = "https://${default_location}-${project_id}.cloudfunctions.net/${function_name}"  # change this
$telegram_token = "4429054:randomstringoflettersandthings"  # change this

gcloud config set project ${project_id}
gcloud functions deploy ${function_name} --runtime python39 --trigger-http --allow-unauthenticated
curl "https://api.telegram.org/bot${telegram_token}/setWebhook?url=${trigger_url}"
