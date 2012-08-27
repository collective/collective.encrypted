Introduction
============

Collective.encrypted is a prototype for implementing client side encrypted
content type and related tools. The basic idea behind it is not to trust
either server or the client to handle completely the security of content. This is
achieved by combining simultaenously the following requisities for
successfully handling content:
1. server side content access right checking
2. client side decryption and encryption of the data that passes the previous

The outcome for this is a balance where the malicious user controlling the
client will be able to work only with limited amount of data. Likewise getting
only partial control over the server will result in minimal results. The only
really viable option for extracting all the data is to have prolonged complete
control over the server, and to phish for the decrypted content for some time
(by eg. altering the web UI). It should be noted that there aren't viable software based security
solutions that would be able to stand that situation. 

Please keep in mind that collective.encrypted is at its present form a **prototype**. 
Constructive criticism and **patches** are more than welcome!

Main Features
=============

At the core of the implementation is the concept of *encryption tag*. It is a
basic content type that represents one usable encryption key. Every encrypted
page must have one or more encryption tags defined. For each, a distinct
encryption key will be queried from the user and used. Encryption tags have
access rights defined in the sharing tab. These access rights will be combined
to the content items using the encryption tag:
* User or group will get all the defined access rights defined in the used
encryption tags if the user or group has at least some access right defined
for all the used encryption tags.

This is meant to be a balance between being very sloppy and very strict about
the required level. If anyone tries to edit the access rights for an encrypted
page the system will recalculate those and revert the sharing tab's content.
Modifying the access rights to any of the encryption tags will cause instantly all the
content items using it reflect the new access rights. Also, there is some
simple deletion protection against deleting an encryption tag item while it is
still in use.

Encryption tags do not contain any part of the key or for instance validation
data. The passwords for deriving the actual keys must be communicated by other
(*secure*) means - which can be either good or bad for overall security depending how
that is handled. With good management policies that can cause more complexity
for malicious users while keeping usable for valid end users.  

The other important part of this product is the *encrypted page*. It is
basically a content item with the content field getting encrypted by some
javascript. The description and title fields will not be protected as to keep
searching and building navigation still possible. The encrypted page will be
assigned one or more encryption tags. They correspond to passwords to be asked
from user.

These passwords will be passed through Pbkdf2, mostly to make key collisions
less likely. The implementation will not bring other benefits of Pbkdf2. The
resulting keys will be XOR'ed to build final encryption key. This is valid
because the entropy of the result will be at least that of the inputs. As a
result the user must either possess all the passwords for the used encryption
tags - or the decryption will fail, or even worse, he will save what will not
be decryptable by other users. 

The encryption itself is aes-256 (ccm) and the results will be handled as hex
strings. To make this all slightly more user friendly the generated keys are
saved in sessionStorage - so that the user will not have to type in them
constantly while navigating around. They will be lost when the window or tab
will be closed.

Screenshots
===========

Editing encrypted content:

.. image:: https://raw.github.com/collective/collective.encrypted/master/sshot-edit.png

Querying for the passwords for two encryption tags:

.. image:: https://raw.github.com/collective/collective.encrypted/master/sshot-query.png

Viewing the content after the decryption has succeeded:

.. image:: https://raw.github.com/collective/collective.encrypted/master/sshot-view.png

Not much to see here, except information about what encrypted pages are using
this tag:

.. image:: https://raw.github.com/collective/collective.encrypted/master/sshot-tag.png

Shared settings of an encrypted page. These are automatically calculated:

.. image:: https://raw.github.com/collective/collective.encrypted/master/sshot-shared.png

Shortcomings
============

At this moment there is no way to easily change the password for an encryption
tag. If a user leaves, or becomes evil out of a sudden, this can be mitigated
by using the access rights (via the sharing tab). However changing the
password for all the content items must be done manually by a person that
knows all the keys used in the content items. This "problem" is caused by the fact that
the keys should never reach the server. There is a solution, to build a proper
json/javascript UI for mass changing the keys on client side. It would work
but I haven't got around to it.

Some parts are missing proper salting. This doesn't destroy the used scheme, but
makes it slightly more suspectible for attacks. Also, as salts must be
communicated to the server (due to the client side scheme not being able to
save them otherwise) their value is slightly diluted.

The solution can at this moment support only symmetric password derived
encryption schemes. This could be improved vastly by introducing the concept
of *wallet*: server holding the encrypted wallet, which client side could
retrieve, manipulate client-side, and save again on the server. Again, this
probably wouldn't be too hard providing it seemed worth doing.

Lack of image encryption is a major shortcoming for users. Sometimes images
used in content items contain a lot of important information. This is well
solvable by some HTML canvas magic, which doesn't seem very hard. A lot
messier will be attempting to get that working with tinyMCE when adding and
image while authoring encrypted page.

There is not much anything that can be done if a user will post nonsensical
data that looks like it's encrypted but is just random. Likewise users can for
instance delete content items, or mess with them otherwise. This is not really
ever preventable completely, but brings to mind that proper *audit logging*
should be built for any environment that is serious about security.

Prerequisities
==============

This product was built for Plone 4.2. The workflow setup should be changed so
that there are no global public read rights for all content items by default. Changing
the default workflow to intranet/extranet is one way to do this. For more
information please see for instance the following link:
- http://plone.org/documentation/kb/setup-a-plone-3-site-with-public-and-restricted-content-1

One possible approach is to be lazy and modify the default simple workflow
published state as follows:

.. image:: https://raw.github.com/collective/collective.encrypted/master/published.png

and after that apply the new setting via the Types control panel:

.. image:: https://raw.github.com/collective/collective.encrypted/master/types.png

Users should be using a recent web browser. The requirement comes from the use of
sessionStorage. This product has been tested with the recent versions of
Firefox and Chrome. Internet Explorer 8+ should support the required features
but this has not been tested. (If there are issues they are probably fixable.)

It is **strongly** recommended that the Plone site should use TLS with valid
trusted keys - either provided by a well known CA or the CA certificates
having securely been deployed by systems administrators. This goes for at
least any site that is aiming for production use.

The quilty
==========

The cryptographic functions are provided by the Stanford Javascript Crypto
Library (GPL).

The two icons are Tango (Public Domain).

The mess of a product was conceived by Cuidightheach (cuidighth@gmail.com).

