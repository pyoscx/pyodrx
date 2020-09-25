# pyodrx
pyodrx is a Python wrapper for generating OpenDRIVE 1.4 xml files. 
Please note that this is not an official implementation.

Work in progress, supported right now is creation of geometries, lanesections (with roadmarker), and junctions including some automation of 
roads that are connected with eachother.


## Getting Started

clone or download the repository.

### Prerequisites

Been tested with Python 3.6.9


### Installing

Go to the pyodrx folder and use

```
pip3 install .
```


## Related work


### esmini
[esmini](https://github.com/esmini/esmini) is a basic OpenSCENARIO player

### pyoscx
[pyoscx](https://github.com/pyoscx/pyoscx) basic python wrapper for OpenSCENARIO 

### spirals

[pyeulerspiral](https://github.com/stefan-urban/pyeulerspiral), used this lib for calculating euler spirals

## Authors

* **Mikael Andersson** - *Initial work* - [mander76](https://github.com/mander76)

* **Irene Natale** - *Inital work* - [inatale93](https://github.com/inatale93)

## Data formats
The wrapper is based on the OpenDRIVE standard.