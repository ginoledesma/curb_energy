Glossary
========

.. glossary::

    auth token
        An `OAuth2 <https://oauth.net/2/>`_ token used to authenticate with
        the `Curb REST API <http://docs.energycurb.com/>`_. The token may be
        either an access token or refresh token. Tokens should be treated
        like passwords -- keep them safe and secure!

    profile
        A set of configuration options that collectively defines how to
        interpret data, and access real time data.

    register
        A source of power measurement data, such as a circuit breaker.

    register groups
        A collection of registers, logically grouped for a specific purpose,
        such as "use", "mains", "solar", or "grid".

    sensor
        An energy monitoring device, which in this case is the Curb Hub. A
        sensor will have one or more registers associated with it.

    sensor group
        A collection of sensor (Curb) devices, grouped in a logical manner,
        such as "Main Panel". A given sensor will usually have at most 18
        registers, and multiple sensors may be needed to cover numerous
        circuit breakers/electric panels in a given location.
