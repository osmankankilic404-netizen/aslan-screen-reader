# Building Developer Documentation for Aslan

Before building developer documentation, [create your developer environment](./createDevEnvironment.md).

## Building developer documentation

To generate the Aslan developer guide, type:

```cmd
scons developerGuide
```

The developer guide will be placed in the `devDocs` folder in the output directory.

To generate the HTML-based source code documentation, type:

```cmd
scons devDocs
```

The documentation will be placed in the `Aslan` folder in the output directory.

## Building aslanHelper developer documentation

To generate developer documentation for aslanHelper (not included in the devDocs target):

```
scons devDocs_aslanHelper
```

The documentation will be placed in the folder `<projectRoot>\output\devDocs\aslanHelper`.
This requires having Doxygen installed.
