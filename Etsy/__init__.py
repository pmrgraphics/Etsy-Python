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

    def __init__(self, creds_file=None, password=None, json=None):
        """
        Initializes the object and loads credentials file specified
        so long as the correct password is supplied. 

        Checks for locally cached Methods.json in order to create
        a dictionary for all of the API Methods

        Args:
            creds_file: string. credential file created previously
            password: string. password used to decrypt file
            json: string. /path/to/file for local JSON storage 
                  defaults to './Methods.json'
        Returns:
            Authorized credentials object to make calls defined
            in Etsy class
        """
        params = {}             
        if creds_file and password:
            creds = decrypt.decrypt(creds_file, password)
            consumer_key = creds['consumer_key']
            client_secret = creds['client_secret']
            oauth_token = creds['oauth_token']
            oauth_token_secret = creds['oauth_token_secret']
            self.params = {'api_key': consumer_key}
            self.OAuth_Full = OAuth1(consumer_key,
                                     client_secret=client_secret,
                                     resource_owner_key=oauth_token,
                                     resource_owner_secret=oauth_token_secret)

        if json:
            Methods_File = json
            with open(Methods_File) as JSON_Data:
                MethodsDict = self.CompileMethods(Methods_File)
        else:
            Methods_File = './Methods.json'
            try:
                with open(Methods_File, 'rb') as JSON_Data:
                    MethodsDict = self.CompileMethods(Methods_File)
            except IOError:
                print("No Methods file found, creating Methods.json")
                self.getMethodTable()
                MethodsDict = self.CompileMethods(Methods_File)



        # except IOError:
        #   print('Cannot open %s, please check the file.') % creds_file

    def get_user_info(self, user):
        """
        Fetches user information from the Etsy API
        Used mainly for testing purposes currently.

        Args:
            user: string. can be any user, calling with
                  '__SELF__' pulls the resource_owners information.

        Returns:
            JSON Information about the selected user.
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
        API and save it to the local working directory for later use by
        the script.

        Args:
            None

        Returns:
            None
        """
        Methods_File = './Methods.json'
        URI = '/'
        response = self.api_call(URI)
        with open(Methods_File, 'wb') as JF:
            json.dump(response, JF)

    #def GetInfo(self, Call):
        """
        Gets info about a specific Etsy API and returns it to the user

        Args:
            Call: string. Which function the user wants more information about

        Returns:
            Info about the API Method to the user.
        """
    

        
    def getListAll(self):
        """
        Returns a list of all the current Etsy API Methods available
        as found by using the locally loaded Dictionary file.

        Args:
            None

        Returns:
            None
        """
        MethodsList = []
        for Each_Method in self.MethodsDict:
            MethodsList.append(Each_Method)
        print("""
        Here is a list of all of the API Methods available for the Etsy API.
        
        If you need more information, running 'getInfo(call)' where call is the
        name of the function you wish to know more details about. 
        """)
        MethodsStr = str(MethodsList).replace("', u'", " ")
        MethodsStr = MethodsStr.replace("[u'", "")
        MethodsStr = MethodsStr.replace("']", "")
        print(MethodsStr)



    def CompileMethods(self, Methods_File):
        """
        Compiles the methods from JSON Data and returns the parsed data
        in a callable MethodsDict dictionary type object for further use 
        by this script.

        Args:
            Methods_File: string. Name of JSON file where Methods will be
            parsed from.
        Returns:
            Dictionary type object that contains the parsed methods 
        """
        self.MethodsDict = {}
        with open(Methods_File, 'rb') as JF:    
            JSON_Data = json.load(JF)
        for Each_Method in JSON_Data['results']:
            self.MethodsDict.update(
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
        
        return self.MethodsDict

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

        response = self.api_call(URI=URI, params=params, oauth=oauth)
        return response

    def api_call(self, URI=None, method='get', oauth=None,
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
