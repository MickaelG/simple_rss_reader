<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Suivi des flux RSS</title>
</head>
<style>
a:link {text-decoration:none; color:black}
a:hover {text-decoration:underline}
a:visited {color:grey}
.date { text-align:right; margin-right:200px; font-weight:bold }
.content { max-width:1000px; margin-left:auto; margin-right:auto }
.link { margin-left:16px; text-indent:-16px; line-height:150% }
.link_bloc { }
</style>
<body>
% for msg in errors:
    {{msg}}</br></a>
% end
<div class=content>
% for links_for_day in links:
<div class=date>{{links_for_day["date"]}}</div>
<div class=link_bloc>
%     for link in links_for_day["links"]:
<div class=link><img src="{{link.img_url}}" width=16/> <a href={{link.url}} title="{{link.title}}">{{link.title}}</a></div>
%     end
</div>
% end

</div>
</body>
</html>

