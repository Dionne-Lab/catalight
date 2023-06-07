In this section, I'll describe the addition of the NKT system into the catalight package.

Connection with the equipment:
------------------------------



Integration to Catalight:
-------------------------
The connection between the computer and the hardware is done within its own package. This simplifies catalight by adding some modularity, and I **strongly** advise that developers adding new instruments to catalight develop the communications within a seperate package.

The computer to hardware communication should be its own package.
Integration into Catalight should be handled as a module within the catalight.equipment subpackage.

.. figure:: _static/images/nkt_additions/expt_expt_types.png
