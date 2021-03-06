#
# services.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.cregsync/src/pcp/cregsync/services.py
#
#  run with --help to see available options

import logging
from Products.PlonePAS.utils import cleanId
from pcp.cregsync import utils
from pcp.cregsync import config

SPMT_BASE = 'sp.eudat.eu'

def prepareid(id):
    return cleanId(id)

def preparedata(values, site, additional_org, email2puid):

    logger = logging.getLogger('cregsync.servicedata')

    fields = {}
    for k,v in values.items():
        fields[k] = v

    title = fields['name'].encode('utf8')
    scl = fields['service_complete_link']['related']['href']
    identifiers = [{'type':'spmt_uid',
                    'value': fields['uuid']},
                    ]

    fields['title'] = title
    fields['description'] = fields['description_external']
    if 'localhost' in scl:
        scl = scl.replace('localhost', SPMT_BASE)
    fields['service_complete_link'] = scl
    fields['identifiers'] = identifiers
    # link contacts
    try:
        contact_url = fields['contact_information']['links']['self']
    except TypeError:
        contact_url = None
    if contact_url is not None:
        # first map exceptions
        contact_data = utils.getDataFromSPMT(contact_url)
        contact_email = contact_data['external_contact_information']['email']
        email = config.creg2dp_email.get(contact_email,contact_email)
        # then look up corresponding UID
        contact_uid = email2puid.get(email, None)
        #    if contact_uid is None:
        #        fields['email'] = contact_email
        #        contact_uid = utils.fixContact(site, fields)
        if contact_uid is None:
            logger.warning("'%s' not found - no contact set for '%s'" \
                           % (contact_email, title))
        else:
            fields['contact'] = contact_uid
    # same for the service owner
    try:
        owner_email = fields['service_owner']['email']
    except TypeError:
        owner_email = None
    if owner_email is not None:
        o_email = config.creg2dp_email.get(owner_email,owner_email)
        owner_uid = email2puid.get(o_email, None)
        #    if owner_uid is None:
        #        owner_uid = utils.fixContact(site, fields, contact_type='security')
        if owner_uid is None:
            logger.warning("'%s' not found - no service owner set for '%s'" \
                           % (owner_email, title))
        else:
            fields['service_owner'] = owner_uid
        
    return fields.copy()

def flattenlinks(data):
    """Unpack and inline the embedded links"""
    for field in config.link_fields:
        link = data[field]['related']['href']
        data[field] = link
    details_link = data['links']['self']
    data['links'] = details_link
    return data

def resolveDependencies(site, data):
    """Resolve dependencies by looking up the UIDs of the respective
    services. It is assumed that the services are there and can be
    looked up by name in the 'catalog' folder."""
    deps = data['dependencies_list']['services']
    if not deps:
        data['dependencies'] = []
    else:
        dependencies = []
        for dep in deps:
            name = dep['service']['name']
            uid = site['catalog'][cleanId(name)].UID()
            dependencies.append(uid)
        data['dependencies'] = dependencies
    return data

def addImplementationDetails(site, impl, data, logger):
    """Adding implementation details to a service component implementation"""
    logger.debug("addImplemenationDetails called with this data: '%s'" % data)
    id = cleanId('version-' + data['version'])
    if id not in impl.contentIds():
        impl.invokeFactory('ServiceComponentImplementationDetails', id)
        logger.info("Adding service component implementation details '%s' to '%s'" % (id, impl.Title()))
    details = impl[id]
    data['title'] = 'Version ' + data['version']
    data['description'] = 'Implementation details of ' + impl.Title() + ': version ' + data['version']
    data['identifiers'] = [{'type':'spmt_uid',
                            'value': data['uuid']},
                       ]
    raw_config_data = data['configuration_parameters']
    if raw_config_data is not None:        
        config_items = raw_config_data.splitlines()
        keys = [item.split()[0] for item in config_items]
        data['configuration_parameters'] = keys
    else:
        data['configuration_parameters'] = []
    details.edit(**data)
    details.reindexObject()
    site.portal_repository.save(obj=details, 
                                comment="Synchronization from SPMT")
    logger.info("Updated '%s': implementation of '%s'" % (data['title'], impl.Title()))    


def addImplementation(site, component, data, logger):
    """Adding an implementation to a service component"""
    logger.debug("addImplemenation called with this data: '%s'" % data)
    id = cleanId(data['name'])
    if id not in component.contentIds():
        component.invokeFactory('ServiceComponentImplementation', id)
        logger.info("Adding service component implementation '%s' to '%s'" % (id, component.Title()))
    implementation = component[id]
    data['title'] = component.Title() + ' implementation: ' + data['name']
    data['identifiers'] = [{'type':'spmt_uid',
                            'value': data['uuid']},
                       ]
    implementation.edit(**data)
    implementation.reindexObject()
    site.portal_repository.save(obj=implementation, 
                                comment="Synchronization from SPMT")
    logger.info("Updated '%s': implementation of '%s'" % (data['name'], component.Title()))
    details_data = utils.getDataFromSPMT(data['component_implementation_details_link']['related']['href'])
    details = details_data['service_component_implementation_details_list']['service_component_implementation_details']
    if not details:
        logger.info("No implemenation details found for '%s'" % data['title'])
        return
    for detail in details:
        addImplementationDetails(site, implementation, detail, logger)
    

def addComponent(service, site, data, logger):
    """Adding a service component to 'service' described by 'data'"""
    logger.debug("addComponent called with this data: '%s'" % data)
    id = cleanId(data['name'])
    if id not in service.contentIds():
        service.invokeFactory('ServiceComponent', id)
        logger.info("Adding service component '%s' to '%s'" % (id, service.Title()))
    component = service[id]
    data['title'] = "Service component '%s'" % data['name']
    data['identifiers'] = [{'type':'spmt_uid',
                            'value': data['uuid']},
                       ]
    component.edit(**data)
    component.reindexObject()
    site.portal_repository.save(obj=component, 
                                comment="Synchronization from SPMT")
    logger.info("Updated '%s' component of '%s'" % (data['name'], service.Title()))
    implementations_data = utils.getDataFromSPMT(data['service_component_implementations_link']['related']['href'])
    # print implementations_data
    implementations = implementations_data['service_component_implementations_list']['service_component_implementations']
    if not implementations:
        logger.info("No implemenations found for '%s'" % data['title'])
        return
    for implementation in implementations:
        addImplementation(site, component, implementation, logger)
    
    
def addDetails(site, parent, data, logger):
    """Adding service details"""
    if not 'details' in parent.objectIds():
        parent.invokeFactory('Service Details', 'details')
        logger.info("Adding 'details' to '%s'" % parent.getId())
    details = parent.details
    data['title'] = 'Service Details'
    data['description'] = 'Details of the %s service' % parent.Title()
    data = flattenlinks(data)
    data = resolveDependencies(site, data)
    data['identifiers'] = [{'type':'spmt_uid',
                            'value': data['uuid']},
                       ]
    details.edit(**data)
    details.reindexObject()
    site.portal_repository.save(obj=details, 
                                comment="Synchronization from SPMT")
    logger.info("Updated 'details' of '%s'" % parent.getId())
    # adding service components if any
    full_data = utils.getDataFromSPMT(data['links'])
    try:
        scl = full_data.get('service_components_list', None)
    except AttributeError:
        scl = None
    if scl is None:
        logger.info('No service components found for %s' % parent.Title())
        return None
    for sc in scl['service_components']:
        logger.info('Adding service component to %s' % parent.Title())
        addComponent(parent, site, sc['component'], logger)
         
    

def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger('var/log/cregsync_services.log')
    args = argparser.parse_args()
    logger.info("'services.py' called with '%s'" % args)

    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))

    targetfolder = site.catalog
    # returns a list of dicts with service data
    spmt_services = utils.getServiceData(args.path, args.filename)   
    email2puid = utils.email2puid(site)
        
    logger.info("Iterating over the service data")
    for entry in spmt_services:
        shortname = entry['name']
        id = prepareid(shortname)
        if id is None:
            logger.warning("Couldn't generate id for ", values)
            continue
        if id not in targetfolder.objectIds():
            targetfolder.invokeFactory('Service', id)
            logger.info("Added %s to the 'catalog' folder" % id)

        # retrieve data to extended rather than overwrite
        additional = targetfolder[id].getAdditional()
        data = preparedata(entry, site, additional, email2puid)
        logger.debug(data)
        targetfolder[id].edit(**data)
        targetfolder[id].reindexObject()
        site.portal_repository.save(obj=targetfolder[id], 
                                    comment="Synchronization from SPMT")
        logger.info("Updated %s in the 'catalog' folder" % id)
        if args.top: continue
        try:
            data = entry['service_details_list']['service_details'][0]  
            # we assume there is at most one
            addDetails(site, targetfolder[id], data, logger)
        except IndexError:
            pass

    if not args.dry:
        logger.info("Committing changes to database")
        import transaction
        transaction.commit()
    else:
        logger.info("dry run; not committing anything")
            
    logger.info("Done")

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
