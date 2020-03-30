###########
Basic Usage
###########

.. |nark| replace:: ``nark``
.. _nark: https://github.com/hotoffthehamster/nark

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

To use nark in a project, import it, e.g.,::

    import nark

You can play around with items without setting anything up,
but to be useful, you'll want to setup a basic config to tell
|nark|_ where to store items that you want to persist.

Wire something along the lines of:

.. code-block:: Python

   import nark

   nark_config = {
      'db': {
         'engine' = 'sqlite',
         'path' = 'path/to/nark.sqlite',
      }
   }
   controller = nark.control.NarkControl(nark_config)
   controller.standup_store()

Now you can read from the data store, e.g.,

.. code-block:: Python

   records = controller.facts.get_all()

As well as being able to write to it, e.g.,

.. code-block:: Python

   fact = nark.items.Fact()
   controller.facts.save(fact)

This is just a taste of the action.

Because code will naturally outpace any effort to document it, please
refer to the docstrings documentation in the source for more information.

.. |class-Controller| replace:: ``class Controller``
.. _class-Controller: https://github.com/hotoffthehamster/dob-bright/blob/master/dob_bright/controller.py

.. |class-NarkControl| replace:: ``nark.NarkControl``
.. _class-NarkControl: https://github.com/hotoffthehamster/nark/blob/master/nark/control.py

Or, better yet, look at the code for the reference client, |dob|_,
to see how best to work with |nark|_. Start by reading the |class-Controller|_,
which descends from |class-NarkControl|_
and runs through the complete setup process.

