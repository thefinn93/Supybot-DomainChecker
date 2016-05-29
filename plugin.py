###
# Copyright (c) 2016, Finn Herzfeld
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import supybot.log as log
from supybot.commands import wrap
import supybot.conf as conf
import supybot.callbacks as callbacks
import dataset
import requests
from xml.etree import ElementTree

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('DomainChecker')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class DomainChecker(callbacks.Plugin):
    """Provide quick access to check domain availability."""

    threaded = True

    def __init__(self, irc):
        """Initialize the plugin."""
        self.__parent = super(DomainChecker, self)
        self.__parent.__init__(irc)
        self.dbfile = conf.supybot.directories.data.dirize("DomainChecker.db")

    def namecheap(self, method, args={}):
        """Make a request to the namecheap API."""
        args['Command'] = method
        args['ApiUser'] = self.registryValue('ApiUser')
        args['ApiKey'] = self.registryValue('ApiKey')
        args['UserName'] = self.registryValue('ApiUser')
        args['ClientIP'] = "127.0.0.1"

        # When in production, use https://api.namecheap.com/xml.response
        sandbox = ".sandbox" if self.registryValue('sandbox') else ""
        api_base = "https://api%s.namecheap.com/xml.response" % sandbox
        response = requests.get(api_base, params=args)
        log.info(response.url)
        tree = ElementTree.fromstring(response.content)
        return tree

    def check(self, irc, msg, args, domain):
        """<domain>.

        Checks if <domain> is available for purchase.
        """
        response = self.namecheap('namecheap.domains.check', {'DomainList': domain})
        if response.get('Status') == "ERROR":
            for error in response[0]:
                log.error(error.text)
                irc.reply("Error! %s" % error.text)
        results = response.find("{http://api.namecheap.com/xml.response}CommandResponse")
        if results is not None:
            for result in results:
                if result.attrib['Available'] == "true":
                    db = dataset.connect("sqlite:///%s" % self.dbfile)
                    tld = domain.split(".")[-1]
                    prices = db['pricing'].find(tld=tld, category="register", years=1)
                    no_prices = True
                    for price in prices:
                        no_prices = False
                        purchase_url = "https://www.namecheap.com/domains/registration/results.aspx"
                        purchase_url += "?domain=%s&aff=%s" % (domain,
                                                               self.registryValue('affiliate_id'))
                        irc.reply("[%s] Available from %s for %s $%s (%s)" % (domain,
                                                                              price['provider'],
                                                                              price['currency'],
                                                                              price['price'],
                                                                              purchase_url))
                    if no_prices:
                        irc.reply("[%s] Allegedly available (pricing info not found for %s)" %
                                  (domain, tld))
                else:
                    irc.reply("[%s] Unavailable" % (result.attrib['Domain']))
    domain = wrap(check, ['text'])

    def update(self, irc, msg, args):
        """Update the namecheap pricing information."""
        irc.reply("This could take a second....")
        response = self.namecheap('namecheap.users.getPricing', {'ProductType': 'DOMAIN'})
        if response.get('Status') == "ERROR":
            for error in response[0]:
                log.error(error.text)
                irc.reply("Error! %s" % error.text)
        results = response.find("./{http://api.namecheap.com/xml.response}CommandResponse/{http://api.namecheap.com/xml.response}UserGetPricingResult")
        db = dataset.connect("sqlite:///%s" % self.dbfile)
        pricing_table = db['pricing']
        pricing_table.delete(provider="Namecheap")
        categories = {}
        if results is not None:
            for product_type in results:
                for category in product_type:
                    categories[category.attrib['Name']] = 0
                    for product in category:
                        for duration in product:
                            pricing_table.insert(dict(tld=product.attrib['Name'],
                                                      years=duration.attrib['Duration'],
                                                      category=category.attrib['Name'],
                                                      price=duration.attrib['Price'],
                                                      currency=duration.attrib['Currency'],
                                                      provider="Namecheap"))
                            categories[category.attrib['Name']] += 1
                    irc.reply("Loaded category %s (%s bits of pricing infoz)" % (
                             category.attrib['Name'], categories[category.attrib['Name']]))
            irc.reply("Done! Results: ")
    update = wrap(update)

Class = DomainChecker


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
