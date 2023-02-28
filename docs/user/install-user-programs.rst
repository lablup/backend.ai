.. role:: raw-html-m2r(raw)
   :format: html

Install User Programs in Session Containers
===========================================

Sometimes you need new programs or libraries that are not installed in your environment. If so, you can install the new program into your environment.

NOTE: Newly installed programs are not environment dependent. It is installed in the user directory.

Install packages with linuxbrew
-------------------------------

If you are a macOS user and a researcher or developer who occasionally installs unix programs, you may be familiar with `homebrew <https://brew.sh>`. You can install new programs using linuxbrew in Backend.AI.

Creating a user linuxbrew directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Directories that begin with a dot are automatically mounted when the session starts. Create a linuxbrew directory that will be automatically mounted so that programs you install with linuxbrew can be used in all sessions.

Create .linuxbrew in the Storage section.

With CLI:

.. code-block:: console

   $ backend.ai vfolder create .linuxbrew

Let’s check if they are created correctly.

.. code-block:: console

   $ backend.ai vfolder list

Also, you can create a directory using GUI console with same name.


Installing linuxbrew
^^^^^^^^^^^^^^^^^^^^


Start a new session for installation. Choose your environment and allocate the necessary resources. Generally, you don't need to allocate a lot of resources, but if you need to compile or install a GPU-dependent library, you need to adjust the resource allocation to your needs.

In general, 1 CPU / 4GB RAM is enough.

.. code-block:: console

   $ sh -c "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install.sh)"


Testing linuxbrew
^^^^^^^^^^^^^^^^^

Enter the brew command to verify that linuxbrew is installed. In general, to use ``linuxbrew`` you need to add the path where ``linuxbrew`` is installed to the PATH variable.

Enter the following command to temporarily add the path and verify that it is installed correctly.

.. code-block:: console

   $ brew


Setting linuxbrew environment variables automatically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To correctly reference the binaries and libraries installed by linuxbrew, add the configuration to ``.bashrc``. You can add settings from the settings tab.

Example: Installing and testing htop
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To test the program installation, let's install a program called ``htop``. ``htop`` is a program that extends the top command, allowing you to monitor the running computing environment in a variety of ways.

Let's install it with the following command:

.. code-block:: console

   $ brew install htop


If there are any libraries needed for the ``htop`` program, they will be installed automatically.

Now let's run:

.. code-block:: console

   $ htop


From the run screen, you can press q to return to the terminal.

1.6 Deleting the linuxbrew Environment

To reset all programs installed with linuxbrew, just delete everything in the .linuxbrew directory.

Note: If you want to remove a program by selecting it, use the ``brew uninstall [PROGRAM_NAME]`` command.

.. code-block:: console

   $ rm -rf ~/.linuxbrew/*


Install packages with miniconda
-------------------------------

Some environments support miniconda. In this case, you can use `miniconda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/>` to install the packages you want.

Creating a user miniconda-required directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Directories that begin with a dot are automatically mounted when the session starts. Create a ``.conda``, ``.continuum`` directory that will be automatically mounted so that programs you install with miniconda can be used in all sessions.

Create ``.conda``, ``.continuum`` in the Storage section.

With CLI:

.. code-block:: console

   $ backend.ai vfolder create .conda
   $ backend.ai vfolder create .continuum


Let’s check if they are created correctly.

.. code-block:: console

   $ backend.ai vfolder list

Also, you can create a directory using GUI console with same name.


miniconda test
^^^^^^^^^^^^^^

Make sure you have miniconda installed in your environment. Package installation using miniconda is only available if miniconda is preinstalled in your environment.

.. code-block:: console

   $ conda


Example: Installing and testing htop
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To test the program installation, let's install a program called ``htop``. ``htop`` is a program that extends the top command, allowing you to monitor the running computing environment in a variety of ways.

Let's install it with the following command:

.. code-block:: console

   $ conda install -c conda-forge htop

If there are any libraries needed for the ``htop`` program, they will be installed automatically.

Now let's run:

.. code-block:: console

   $ htop

From the run screen, you can press q to return to the terminal.



