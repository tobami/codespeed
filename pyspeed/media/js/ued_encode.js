//ued_encode() will take an array as its argument and return the data encoded in UED format - as a string.
//http://www.openjs.com/scripts/data/ued_url_encoded_data/
function ued_encode(arr,current_index) {
	var query = ""
	if(typeof current_index=='undefined') current_index = '';

	if(typeof(arr) == 'object') {
		var params = new Array();
		for(key in arr) {
			var data = arr[key];
			var key_value = key;
			if(current_index) {
				key_value = current_index+"["+key+"]"
			}

			if(typeof(data) == 'object') {
				if(data.length) { //List
					for(var i=0;i<data.length; i++) {
						params.push(key_value+"[]="+ued_encode(data[i],key_value)); //:RECURSION:
					}
				} else { //Associative array
					params.push(ued_encode(data,key_value)); //:RECURSION:
				}
			} else { //String or Number
				params.push(key_value+"="+encodeURIComponent(data));
			}
		}
		query = params.join("&");
	} else {
		query = encodeURIComponent(arr);
	}

	return query;
}