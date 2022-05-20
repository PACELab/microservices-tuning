require "socket"
local time = socket.gettime()*1000
math.randomseed(time)
math.random(); math.random(); math.random()

local plot_ids = {299534,543103,299537,447404,456740,537915,299536,495925,438650,287947,487297,450465,24428,284054,166428,468224,445629,283995,99861,532671,920,284053,535167,457799,157433,263115,118340,576393,324857,
424783,10195,297802,363088,280217,137113,449562,329996,485811,491418,315635,122917,526050,480414,522681,500852,376865,500682,337339,1726,1771,271110,458723,566555,390634,375588,338952,76338,399579,
512196,245891,347375,10138,287424,335983,671,454294,22,424694,504172,404368,120,395990,458156,440161,301351,579598,442249,218043,383498,487558,298250,454983,263109,3512,460019,284052,122,1585,157336,
446021,464504,459992,361292,155,627,11,428078,339877,351286,463684,407451,11430,429617,672,348350,502292,68721,489925,460885,562,12536,429300,346910,375262,438799,244506,400650,450001,532321,11024,
287948,340676,226857,102899,483906,527261,411728,429351,396806,531309,454227,76617,440472,514439,378236,490132,431530,293660,11451,209112,86467,270010,131631,151960,13186,1949,4922,297762,15789,1724,
254128,480530,127585,2320,574,68817,141052,403119,332562,260513,401246,393519,241257,12289,181808,399402,12123,1116,308504,19995,603,207768,145247,844,77931,320007,266396,272,374473,290751,353326,152780,
341006,9703,316152,97614,278,351339,353616,77948,1667,341012,15370,289222,420817,395458,54318,27205,10925,179826,390062,680,2019,302349,280,11976,8966,10048,369192,381288,111190,12103,88273,5336,
399361,11319,335984,314405,260346,10199,338189,182560,574241,438674,467660,2749,123025,38543,11045,3093,315664,210577,397422,424,218778,9994,10320,374475,830,243940,9662,41211,515248,177494,102780,
155084,353081,250734,471859,252178,16608,127560,428449,330483,10131,10497,329865,55301,375315,9425,121,400535,498248,429197,12444,269149,22787,1930,9021,527641,140607,8342,244786,243938,419479,82390,
198663,11470,675,11050,109445,11549,38541,398175,77663,673,332340,458253,9725,265189,101,233063,1497,309886,31442,198375,11497,49051,243683,11596,223485,524247,453755,6687,10523,12246,76544,93828,
227348,205596,10587,228150,5902,293310,110420,9962,466282,439079,246080,535,11046,10479,526,345940,82702,767,8881,157845,503129,471507,150117,221902,433808,153158,209274,58,10972,168705,382322,3035,
245916,84287,300681,157851,2614,11128,408,2312,74,6522,11186,2322,550,10191,1534,454652,157847,13851,5550,11230,9513,790,245698,345887,12207,26123,172,36647,226486,11967,130150,12118,9064,
1683,517166,11826,318846,74997,339380,10756,24122,10016,242582,66,304357,333339,8984,10466,5511,4176,286217,331962,11866,606,191714,87101,238636,121875,2275,396461,11418,10437,75802,246655,10975,338970,
597,22586,10029,245168,1975,273477,8392,86597,10648,559,527729,10052,397,4477,150689,44114,4978,11880,9754,320288,9538,9530,84165,80038,2623,10481,136,135397,10934,178809,198185,11782,3604,9303,143,
336004,10057,4437,3063,457136,41602,333385,9992,1494,172533,674,12192,1825,8587,10477,131634,324552,6279,24150,564394,435577,87499,443055,238,8869,4964,49017,11527,39210,166426,12445,8689,22949,156022,
190469,18148,10539,11932,103620,10163,9815,295699,9289,177572,25643,11212,65759,38234,5375,8409,8090,93,553100,200505,10610,16577,330947,514692,449985,10731,209276,10623,9741,862,505948,438740,369972,
14536,10518,9053,9972,4961,249,884,9356,324670,1280,8879,12160,327331,10328,9696,11565,321612,2163,77805,50725,643,916,336050,335988,16558,9594,10712,11074,399055,13416,300668,119450,11386,10589,
49026,1552,13944,524309,9385,36419,775,931,77875,10876,10675,543343,9796,11817,11901,49521,228203,261,257445,1730,10632,11864,506,9644,9093,419430,44945,10303,468,16804,1396,2830,442062,1714,10160,17130,
102382,301,3085,11184,10658,9626,140420,205321,9945,12142,38360,10923,9728,10577,9825,281338,512239,10197,24438,8427,347969,649,7548,35552,3525,13,100402,936,56288,9549,11185,10155,1412,11559,
1554,11416,11253,12154,209403,9443,206647,98548,44629,63493,1710,10398,9607,3132,9879,11929,9664,36819,9566,9587,19255,14636,14013,9542,141043,10784,113833,11515,71864,58232,10588,12155,4599,28597,2362,
557,401469,11634,10403,126889,21734,9597,10468,76341,543540,51300,10808,62046,106,204,106646,13067,209263,484247,567604,13576,34480,44147,1023,150540,234200,360920,2665,318121,24056,11562,
73937,10207,10757,1833,2742,10762,250066,245706,6471,2062,11030,1613,10495,50837,2039,11453,85,332,4133,49950,11006,10060,11324,576071,11658,11850,98566,10488,2000,11566,10907,10412,30197,402900,14292,
5820,16899,6878,472451,8764,13595,83,2313,11787,636,13193,12093,604,44716,588001,57158,500904,595680,260,17295,234,12690,1694,780,19833,405774,452832,10136,531,581585,41154,956,13532,351044,9876,595188,
10985,11469,11377,13291,10242,887,21755,4105,10494,353576,181533,854,449924,607,499533,6623,10681,16869,49012,9612,218,4244,10152,2925,103328,8010,324786,424139,285,584804,483157,11560,10956,585,
1865,8092,569064,101173,9087,9464,11260,8882,9515,34769,11197,97051,983,445651,447332,11686,426543,646,293,7300,11374,63815,679,11051,238628,268896,631,38363,1880,11141,11158,10186,4520,1792,10122,9909,
119675,185,9966,64639,1406,259316,512954,940,11854,2771,704,257344,16642,175,71668,608,10909,287,10758,953,621,11824,10414,262500,9766,14072,27585,632,575766,372058,225886,593325,293167,132316,11178,
493922,64586,18570,553141,37414,129,336843,273248,10720,438,14506,8398,348,812,401981,8491,590927,8386,447200,449443,2928,9333,11078,857,376565,10326,9777,399360,11797,6691,21334,9589,4515,8592,76487,
23706,626,8046,19123,19426,12877,545919,350,9516,769,508763,9918,51241,302,14048,310,194662,1487,376540,10538,598073,26280,12107,17927,12508,14410,9611,10890,11983,14976,84306,7862,50797,605,9957,1422,
13973,359940,13920,500664,9410,339964,425591,598549,449563,10069,9942,577109,10823,31175,363,13250,12140,297761,8270,44129,55725,10053,11252,11894,2639,354912,808,315837,570426,10564,475888,8088,
14052,68924,427641,98,43959,14197,13252,18079,1368,10843,45657,4967,37724,954,10741,598062,595409,12177,1979,458344,201088,10543,38031,11973,564,13159,10849,7095,103,26900,13279,241251,8987,6309}

request = function()
  local plot_idx= math.random(1,4)
  local plot_id = tostring(plot_ids[plot_idx]) --tostring(math.random(1,100))
  
  local args = "plot_id=" .. plot_id
  local method = "GET"
  local headers = {}
  headers["Content-Type"] = "application/x-www-form-urlencoded"
  -- Use your cluster-ip here:
  --local path = "http://localhost:8080/wrk2-api/user-timeline/read?" .. args
  local path = "http://userv2:8080/wrk2-api/plot/read?" .. args
  return wrk.format(method, path, headers, nil)

end
