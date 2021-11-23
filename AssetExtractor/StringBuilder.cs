// namespace AssetStudio {
// 	public class StringBuilder {
// 		private string contents;
// 		public StringBuilder() {
// 			contents = "";
// 		}
// 		public void AppendLine(string content) {
// 			contents += content + "\n";
// 		}
// 		public void AppendFormat(string format, params object[] values) {
// 			var to_append = format;
// 			for(int i = 0; i < values.Length; i++) {
// 				var current = "{" + i.ToString() +"}";
// 				to_append = to_append.Replace(current, values[i].ToString());
// 			}
// 			contents += to_append;
// 		}
// 		public void Replace(string from, string to) {
// 			contents = contents.Replace(from, to);
// 		}
// 		public void ToString() {
// 			return contents;
// 		}
// 	}
// }