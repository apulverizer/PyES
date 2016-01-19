# PyES (Python Email Scraper)

This is a Python2 script relying on the Google Gmail Python API and the Goose-Extractor library. It is designed to read emails, parse out urls, open the urls (pointing to articles), extract the article text and title, then store the article info in a json file. It then marks the email as read.

Follow the steps outlined [here](https://developers.google.com/gmail/api/quickstart/python) to set up the Gmail API Python bindings and authentication.

**NOTE:** You will want to change the SCOPES variable to use https://www.googleapis.com/auth/gmail.modify rather than https://www.googleapis.com/auth/gmail.readonly. You will also want to change the application name to whatever you want to call this script (PyES, for example).

Once you run the sample provided by Google, your credentials will be stored locally, so you will not have to authenticate your account in the future. It seems to only remember the current permissions that is why you need to adjust the SCOPES before running it. Otherwise you'll have to make a new project and set up the authentication again.

Then install [goose-extractor](https://pypi.python.org/pypi/goose-extractor/). This library uses beautifulsoup to extract articles from websites.

Now that you have everything setup. You can run PyES.py:

```python
python PyES.py <directory_to_store_files> <gmail_account_email_address> <gmail_query>

- directory_to_store_files: Where to store the json files about each article (eg. "C:\stuff")
- gmail_account_email_address: The account to use; account must have API enabled (eg. "apulverizer@gmail.com")
- gmail_query: The query to use to find specific emails. (eg "labels:Fire is:unread")

```

Output is of the form:

```json
{
	"url": "",
	"text": "",
	"datetime": 0,
	"message_id": "",
	"title": ""
}
```



