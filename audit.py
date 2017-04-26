import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
from num2words import num2words

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
PHONE_7_NUM = re.compile(r'^\d{7}$')
PHONE_10_NUM = re.compile(r'^\d{10}$')
PHONE_11_NUM = re.compile(r'^\d{11}$')
POSTCODE = re.compile(r'^\d{5}$|\d{5}-\d{4}$')

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Circle", "Crescent", "Gate", "Terrace", "Grove", "Way"]

mapping = {
            "St": "Street",
            "St.": "Street",
            "STREET": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Dr.": "Drive",
            "Dr": "Drive",
            "Rd": "Road",
            "Rd.": "Road",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Ln": "Line",
            "Ln.": "Line",
            "Trl": "Trail",
            "Cir": "Circle",
            "Cir.": "Circle",
            "Ct": "Court",
            "Ct.": "Court",
            "Crt": "Court",
            "Crt.": "Court",
            "By-pass": "Bypass",
            "N.": "North",
            "N": "North",
            "E.": "East",
            "E": "East",
            "S.": "South",
            "S": "South",
            "W.": "West",
            "W": "West"
          }


word_number_mapping = {
                     "First": "1st",
                     "first": "1st",
                     "Second": "2nd",
                     "second": "2nd",
                     "Third": "3rd",
                     "third": "3rd",
                     "Fourth": "4th",
                     "fourth": "4th",
                     "Fifth": "5th",
                     "fifth": "5th",
                     "Sixth": "6th",
                     "sixth": "6th",
                     "Seventh": "7th",
                     "seventh": "7th",
                     "Eighth": "8th",
                     "eighth": "8th",
                     "Ninth": "9th",
                     "ninth": "9th",
                     "Tenth": "10th",
                     "tenth": "10th"
                   }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit_street(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name):
    """
    Clean street name for insertion into SQL database
    """
    better_name = name
    for key in mapping.keys():
      better_name = re.sub(r'\s' + re.escape(key) + r'$', ' ' + mapping[key], better_name)

    for key in word_number_mapping.keys():
      better_name = re.sub(key, word_number_mapping[key], better_name)

    # Check last words as avenue, road, street, etc. are capitalized
    last_word = better_name.rsplit(None, 1)[-1]
    if last_word.islower():
        better_name = re.sub(last_word, last_word.title(), better_name)
    #print better_name
    return better_name

def update_phone_num(phone_num):
    """
    Clean phone number
    """

    #original_phone_num = phone_num  ##uncomment this line for debug

    # Remove +1, -, whitespaces, . or + from phone numbers
    phone_num = re.sub("\+1", "", phone_num)
    phone_num = re.sub("-", "", phone_num)
    phone_num = re.sub("[()]", "", phone_num)
    phone_num = re.sub("\s", "", phone_num)
    phone_num = re.sub("\\.", "", phone_num)
    phone_num = re.sub("\\+", "", phone_num)

    # Standard phone format (spf): +1 (408)###-####
    # After cleaning, there are 3 situation
    # Situation 1: Convert 10 digits number to spf
    m_ten = PHONE_10_NUM.match(phone_num)
    if m_ten is not None:
      phone_num = '+1(' + phone_num[:3] + ')' + phone_num[3:6] + '-' + phone_num[6:10]
    # Situation 2: Convert 7 digits number to spf
    m_seven = PHONE_7_NUM.match(phone_num)
    if m_seven is not None:
      phone_num = '+1(408)' + phone_num[1:3] + '-' + phone_num[3:7]
    # Situation 3: Convert 11 digits number to spf
    m_eleven = PHONE_11_NUM.match(phone_num)
    if m_eleven is not None:
      phone_num = '+' + phone_num[:1] + '(' + phone_num[1:4] + ')' + phone_num[4:7] + '-' + phone_num[7:11]

    # Check all the matching requirements
    if (m_seven is not None) or (m_ten is not None) or (m_eleven is not None):
      return phone_num
    else:
        #print "wrong phone number: ", original_phone_num  ##uncomment this line for debug
        return None

def update_postal_code(postcode):
    """
    Clean postal code
    """

    # Remove CA and whitespace from original postal code
    postcode = re.sub("CA", "", postcode)
    postcode = re.sub("\s", "", postcode)

    # Use regex to match postal code
    m = POSTCODE.match(postcode)
    if m is not None:
      postcode = 'CA ' + postcode
      return postcode
    else:
      #print "WRONG POSTAL CODE:", postcode
      return None





