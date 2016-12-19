"""
Client package for interacting with Etsy's API

"""
__author__ = 'siorai@gmail.com (Paul Waldorf)'


# Standard imports
import json
import logging
import requests
import pickle


# Non-standard imports
from requests_oauthlib import OAuth1
from urlparse import parse_qs
from urllib import urlencode


# Local imports
# import Etsy-Python
import Credential_maker
import decrypt


log = logging.getLogger(__name__)


class EtsyPasswordError(Exception):
    """
    Password error handling
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Etsy(object):
    """
    Class creating and making calls for the Etsy API
    by creating an authorized object with an encrypted
    credentials file and password for decrypting.
    """

    def __init__(self, creds_file=None, password=None):
        """
        Initializes the object and loads credentials file specified
        so long as the correct password is supplied.

        Args:
          creds_file: string. credential file created previously
          password: string. password used to decrypt file

        Returns:
	  Authorized credentials object to make calls defined
          in Etsy class
          
        """
	if creds_file and password:
	  creds = decrypt.decrypt(creds_file, password)
	  consumer_key = creds['consumer_key']
          client_secret = creds['client_secret']
	  oauth_token = creds['oauth_token']
	  oauth_token_secret = creds['oauth_token_secret']
          self.params = {'api_key': consumer_key}
          self.Method_Dict = {}
          self.OAuth_Full = OAuth1(consumer_key,
                                   client_secret=client_secret,
                                   resource_owner_key=oauth_token,
                                   resource_owner_secret=oauth_token_secret)

        # except IOError:
        #   print('Cannot open %s, please check the file.') % creds_file

    def get_user_info(self, user):
        """
	
        """
        URI = '/users/%s' % user
        Auth = {}
        if user == '__SELF__':
          Auth = {'oauth': self.OAuth_Full}
        response = self.api_call(URI, **Auth)
        return response

    def getMethodTable(self):
        """
        Get a complete list of all of the methods available to the Etsy
        API
        """
        URI = '/'
        response = self.api_call(URI)
	return response

    def CompileMethods(self):
        # self.MethodsDict = {}
        API_Method_Response = self.getMethodTable()
        for Each_Method in API_Method_Response['results']:
          self.Method_Dict.update(
                                   {Each_Method['name']:
                                    {'Name': Each_Method['name'],
                                     'URI': Each_Method['uri'],
                                     'Visibility': Each_Method['visibility'],
                                     'HTTP_Method': Each_Method['http_method'],
                                     'Parameters': Each_Method['params'],
                                     'Defaults': Each_Method['defaults'],
                                     'Type': Each_Method['type'],
                                     'Description': Each_Method['description'],
                                    }
                                   }
                                 )
        return self.Method_Dict

    def ListOfMethods(self):
	ListOfMethods = self.Method_Dict.keys()
        print(ListOfMethods)

    def findAllShopReceipts(self, shop_id, offset=None):
        """
        Method for returning all of the receipts for a given Etsy Shop.
        Since the Etsy API limits the amount of reciepts you can request in
        a single call, multiple api calls may be needed to gather the amount
        of receipts needed. As of this writing the maximum amount of reciepts
        is capped at 100 per call.

        Args:
            shop_id: string. Unique shop identifier as indicated from etsy
            offset: string. Offset the results by a given amount

        Returns:
            JSON data as recieved from the Etsy API
        """

        URI = 'shops/%s/receipts/' % shop_id
        params = {}
        params['shop_id'] = shop_id
        oauth = {'oauth': self.OAuth_Full}
        if offset:
            params['offset'] = offset

        response = self.api_call(URI, params=params, oauth=oauth)
        return response

    def api_call(self, URI, method='get', oauth=None,
                 params=None, files=None):
	"""
        Calls the Etsy API

        Args:
            URI: Specific url extention to be added to the end of the base url
                that will change depending on what kind of action requested
            oauth: passes oauth authentication if needed by the method
            params: passes parameters if needed
            files: passes files if needed

        Returns:
            json data returned from server in response

        """
        Base_URL = "https://openapi.etsy.com/v2"
	hooks = {}
	if oauth:
	  hooks = {'auth': oauth}
          if params is None:
            params = {}
        else:
          if params is None:
	    params = self.params
          else:
            params.update(self.params)

        Full_URL = "%s%s" % (Base_URL, URI)
        querystr = urlencode(params)
        if querystr:
            Full_URL = "%s?%s" % (Full_URL, querystr)
        response = getattr(requests, method)(Full_URL, files=files, **hooks)

        try:
            return json.loads(response.text)
        except (TypeError, ValueError):
            return response.text

