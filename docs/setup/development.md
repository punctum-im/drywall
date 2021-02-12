# Setting up for development

1. Clone the latest sources. For development purposes, you'll most likely want to pull the ``develop`` branch:

    ```shell
    $ git pull https://github.com/punctum-im/drywall -b develop
    ```

2. Install drywall as a module (this will automatically pull dependencies!):

    ```shell
    $ pip3 install .
    ```

    > Note: You should use user installation for this. Newer versions of pip default to user presentation when they can't install to the global site-packages; users of older versions must pass the ``--user`` command line argument.

And you're done! To start up your drywall instance, run ``./run.sh`` from the directory you cloned drywall's source code to.

## Troubleshooting

- You may sometimes need to re-do ``pip3 install .`` if ``pytest`` stops working correctly.
