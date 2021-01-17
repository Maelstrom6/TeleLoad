$project_id = "some-google-project-id"  # change this
$function_name = "receiver"  # change this
$telegram_token = "4429054:randomstringoflettersandthings"  # change this
$trigger_url = "https://location-${project_id}.cloudfunctions.net/${function_name}"  # change this

gcloud config set project ${project_id}
gcloud functions deploy ${function_name} --runtime python39 --trigger-http --allow-unauthenticated
curl "https://api.telegram.org/bot${telegram_token}/setWebhook?url=${trigger_url}"
