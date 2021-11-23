// See https://aka.ms/new-console-template for more information
using AssetStudio;
using System.IO;
string[] filePaths = Directory.GetFiles(@"/Users/liz3/Projects/genshinStuff/out/", "*.bin", SearchOption.AllDirectories);
int count = 0;
foreach(string e in filePaths) {
	var reader = new FileReader(e);
	var manager = new AssetsManager();
	var f = new SerializedFile(reader, manager);
	  foreach (var objectInfo in f.m_Objects)
	  {
		   var objectReader = new ObjectReader(reader, f, objectInfo);
		   if(objectReader.type == ClassIDType.Mesh) {
		   		var instance = new Mesh(objectReader);
		   		Exporter.ExportMesh(new AssetItem(instance, count++), "/Users/liz3/Projects/genshinStuff/out2/");
		
		   }
	                  
	   }

}
