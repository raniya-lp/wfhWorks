from . import models
def pattern_subsection_creation(pattern_section,pattern):
    for i in pattern_section:
        pattern_section=models.PatternSection.objects.create(pattern=pattern,name=i['section'],has_sub_section=i["has_sub_section"],section_type=i["section_type"],section_icon=i["section_icon"],level=i["level"])
        section_collection=[]
        section_collection_list=[]
        if i["has_sub_section"]:
            for j in i["sub_section_list"]:
                pattern_sub=models.PatternSubSection.objects.create(pattern_section=pattern_section,name=j["sub_section"],level=j["level"])
                if i["section_type"] =='list':
                    section_collection =[models.PatternSectionCollection(pattern_sub_section=pattern_sub,data_list=j["data"])]
                    section_collection_list.extend(section_collection)
                elif i["section_type"] =='text':
                    section_collection =[models.PatternSectionCollection(pattern_sub_section=pattern_sub,data_text=k)for k in j["data"]]
                    section_collection_list.extend(section_collection)
                else:
                    
                    section_collection =[models.PatternSectionCollection(pattern_sub_section=pattern_sub,data_image=k.update({"title":None,"description":None})) if len(k.keys())<2 else models.PatternSectionCollection(pattern_sub_section=pattern_sub,data_image=k) for k in j["data"]] 
                    section_collection_list.extend(section_collection)
        else:
            if i["section_type"] =='list':
                section_collection =[models.PatternSectionCollection(pattern_section=pattern_section,data_list=i["data"])]
                section_collection_list.extend(section_collection)
            elif i["section_type"] =='text':
                section_collection =[models.PatternSectionCollection(pattern_section=pattern_section,data_text=k)for k in i["data"]]
                section_collection_list.extend(section_collection)
            else:
                section_collection =[models.PatternSectionCollection(pattern_section=pattern_section,data_image=k.update({"title":None,"description":None})) if len(k.keys())<2 else models.PatternSectionCollection(pattern_section=pattern_section,data_image=k) for k in i["data"]] 
                section_collection_list.extend(section_collection)
        models.PatternSectionCollection.objects.bulk_create(section_collection_list)