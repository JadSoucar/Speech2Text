Instructions
1. Run Docker Image and specify port 
2. Use the /eng2arp/<words>/<output>
- Where words is a string of english word/s to be translated to arpabet
- Where output is either "dic" or "string"

For example 
eng2arp/Hello Hello There/dic
{"Hello": arp_translation, "There": arp_translation}
*note that if the output is dic, the dic will contain all unique words

eng2arp/Hello Hello There/dic
{arp_translation of Hello} {arp_translation of Hello} {arp_translation of There}
*note that each word will be returned within brackets
