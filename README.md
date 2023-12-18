# MeshToPointClouds-Houdini
A python shelf tool to convert mesh to point clouds using Houdini.

https://github.com/aniketrajnish/MeshToPointClouds-Houdini/assets/58925008/2ee677dc-05d4-4988-bc64-b5f4941af769

## Usage
* Clone the repository
  ```
  git clone https://github.com/aniketrajnish/MeshToPointClouds-Houdini.git
  ```
* Open/Create a Houdini project.
* Create a new shelf tool in Houdini.
* Paste the python script `src/MeshToPCs.py` to the shelf tool's script.
* Create a new geometry in houdini/import a 3d mesh.
*  Click on the python shelf to launch the tool and follow the following instructions:
   ```
   Select geometry container -> Select number of point clouds
   -> Try searching for texture automatically/manually -> Let it cook 🫦
   ```

## Contributing
Contributions to the project are welcome. Currently working on:
* Developing a pipeline to export the point cloud using [pcexport](https://www.sidefx.com/docs/houdini/vex/functions/pcexport.html).
* Improving the automatic search.

## License
MIT License
