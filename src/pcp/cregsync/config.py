# explicit mappings of creg ids to dp ids

cid2dpid = {
    4:'CINECA',
    5:'CSC',
    6:'ucines',
    7:'STFC',
    8:'SURFsara',
    9:'SIGMA--UiO',
    10:'KIT',
    11:'mpcdf',
    12:'UEDIN--EPCC',
    13:'MPI--PL',
    14:'PSNC',
    15:'DKRZ',
    16:'EKUT',
    17:'INGV',
    18:'JUELICH',
    19:'UCL',
    20:'SNIC',  # or should this be called PDC?
    21:'BSC',
    161:'GRNET',
    181:'TRUST--IT',
    201:'GFZ',
}

# map creg:site keys to dp:provider keys
# the default is to use creg keys in lower case directly

sitekeys2dp = {
    'description':'text',
    'alarmemail':'alarm_email',
    'emergencytel':'emergency_phone',
    'helpdeskemail':'helpdesk_email',
    'homeurl':'url',
    'iprange':'ip4range',
    'officialname':'description',
}