# Supybot DomainChecker plugin
Check the availability of a domain via IRC. Uses the Namecheap API

## Setup

### Set your API keys
After loading the plugin, you'll need to set at least two config options:

* `plugins.DomainChecker.ApiKey` should be set to your [Namecheap API key](https://ap.www.namecheap.com/Profile/Tools/ApiAccess). Make sure your bot's IP is whitelisted!
* `plugins.DomainChecker.ApiUser` should be set to your Namecheap username.

Some optional configs:

* `plugins.DomainChecker.affiliate_id` is the Namecheap Affiliate ID to use in the purchase link. It defaults to mine, leave it to support this incredibly complex software that I spent *nearly an hour* of my life on.
* `plugins.DomainChecker.sandbox` if set to true will use the Namecheap sandbox. There's basically no reason to set this unless you're developing this plugin further.

### Update the pricelist
Next, go and update the pricelist. Send the bot `domainfinder update`. It will take a few minutes to download the namecheap price list, then give you a report back.

## Usage
Usage is pretty straightforward, just run `domain <domain>` and it'll reply with the availability of the domain. eg:

```
<thefinn93>      testbot: domain dankmemes.net
<testbot>        thefinn93: [dankmemes.net] Available from Namecheap for USD $11.98 (https://www.namecheap.com/domains/registration/results.aspx?domain=dankmemes.net&aff=80599)
```
