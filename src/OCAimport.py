
# """
# Resolve OCA importer
# For the moment this preference should be set manually :
# Preferences>User>editing>Standard still duration = 1 frame
# Otherwise the script doesnt seem to set the duration correctly.

# QUESTIONS
# - How to change fusion (existing) FuID nodes parameters in python (ex: merge's ApplyMode parameter) ?
# It works in lua, So I use this workaround: composition.Execute(v.Name + '.ApplyMode = "Multiply"')
# - no resolve.GetPrefs()?
# - mediapool.MoveClips doesn't seem to work...
# - set clip name not possible on existing clips : https://forum.blackmagicdesign.com/viewtopic.php?t=156136&p=989212

# TODO:
# - check Preferences>User>editing>Standard still duration (there is fu.GetPrefs() but no resolve.GetPrefs()?)
# - (optional) add multiplane using a 3D merge/imageplanes/render
# - (optional) parse oca blending mode (not sure how this can be used with the 3d space)
# - (optional) add mediaouts to expose layer masks for color grading
# If not using fusion, color module can be used directly... (no option checked) 
# But the choice may arise later so it would be better to always do the full setup
# The performance should be tested.
# - Import camera from gltf or USD
# - Import keyframe animation from gltf or USD for camera and layers
# - create sub-bins to hide method's internal junk

# DONE
# - fix still images durations https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=196370 (see blow)
# > with duplicates
# > with compound clips
# > Precomp in Edit page
# > Precomp in Fusion (CreateFusionClip)


# TODO
# > InsertFusionGeneratorIntoTimeline(generatorName)

#############################################################################################################
# HOW to fix still images durations ?
# https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=196370 
# insert many single frames ? That's the current workaround
# Many good suggestions to workaround this from Andrew Hazelden :
# *** For some timeline creation options it is helpful to build an EDL then import it.
# There is a bit of funkiness on relinking media from an EDL with the conform bin feature.

# *** Make an effects template/generator macro that drops into the edit page to bring in media. 
# https://vfxstudy.com/tutorials/macros-templates/
# Create fusion nodes, createa macro expose parameters 
# macro is saved in C:\Users\Julien\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros
# and copy in template folder
# C:\Users\Julien\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit 
# or 
# C:\Users\Julien\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Fusion
# Restart resolve NOPE
# https://forum.blackmagicdesign.com/viewtopic.php?f=22&t=108818
# https://youtu.be/IBv4wGVraBs?t=255
# To use in the edit page you 1 i 1 o at least!!
# > macro building esentials https://www.steakunderwater.com/wesuckless/viewtopic.php?p=11590
# > stillImageLoad only shows in fusion, not edit page's effets ?
# > copy C:\Program Files\Blackmagic Design\DaVinci Resolve\Fusion\Templates\Templates.drfx which is a zip
# in P:\workflow\dev\blackmagic\templates\default\
# extract it and add stillImageLoader.setting in Edit\Generators
# create a new archive Templates zip and rename in Templates.drfx
# replace C:\Program Files\Blackmagic Design\DaVinci Resolve\Fusion\Templates\Templates.drfx (backup the original first)
# > another template tut https://www.youtube.com/watch?v=NZQCHSSqn_0
# > another template tut https://www.youtube.com/watch?v=wj_tbMr9Ypw
# > https://resolve.cafe/developers/fusiontemplates/
# ???????????
# > now how to add Template to timeline by script ?
# https://www.reddit.com/r/davinciresolve/comments/17pzb3h/can_we_add_a_fusion_template_to_timeline_via/
# no answer...
# https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=137014&p=738673&hilit=script+Fusion+Templates#p738673
# no answer...
# https://forum.blackmagicdesign.com/viewtopic.php?f=22&t=75356&p=470652&hilit=script+Fusion+Templates#p470652
# but that's to script fusion comp
# ???????????
# > ANSWER!
# InsertOFXGeneratorIntoTimeline InsertFusionGeneratorIntoTimeline InsertGeneratorIntoTimeline InsertFusionCompositionIntoTimeline !

# *** A fuse can be put into a wrapper macro.
# C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Fusion\Fuses
# doesn't exist but :
# C:\Users\Julien\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Fuses
# ex : copy P:\workflow\dev\blackmagic\fuses\BryanRayFuses\Fuses\Clones\FuseTransform.Fuse to Fuses folder

# *** An OpenFX plugin could be made to do the OCA rendering task on the fly. 
# Then the ofx plugin could have a oca filename, frame offset/start frame/end frame set of controls.
# C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\OpenFX

# *** I don't know if you've seen any of the Vonk Ultra/OCA data node efforts I did in Resolve/Fusion?
# Vonk has direct image loader/saver fuses, json file readers, etc.
# """
#############################################################################################################

#############################################################################################################
# Usefull references
# https://resolve.cafe/developers/scripting/
# C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Workflow Integrations\README.txt
# https://gist.github.com/X-Raym/2f2bf453fc481b9cca624d7ca0e19de8?permalink_comment_id=4315832
#############################################################################################################

import json
import os

 # All but default (fusion) preferences
from pprint import pprint
# pprint(fu.GetPrefs(None, False))

# from python_get_resolve import GetResolve
# resolve = GetResolve()
projectManager = resolve.GetProjectManager()

COMPOSITE_NORMAL, COMPOSITE_ADD, COMPOSITE_SUBTRACT, COMPOSITE_DIFF, COMPOSITE_MULTIPLY, COMPOSITE_SCREEN, COMPOSITE_OVERLAY, COMPOSITE_HARDLIGHT, COMPOSITE_SOFTLIGHT, COMPOSITE_DARKEN, COMPOSITE_LIGHTEN, COMPOSITE_COLOR_DODGE, COMPOSITE_COLOR_BURN, COMPOSITE_EXCLUSION, COMPOSITE_HUE, COMPOSITE_SATURATE, COMPOSITE_COLORIZE, COMPOSITE_LUMA_MASK, COMPOSITE_DIVIDE, COMPOSITE_LINEAR_DODGE, COMPOSITE_LINEAR_BURN, COMPOSITE_LINEAR_LIGHT, COMPOSITE_VIVID_LIGHT, COMPOSITE_PIN_LIGHT, COMPOSITE_HARD_MIX, COMPOSITE_LIGHTER_COLOR, COMPOSITE_DARKER_COLOR, COMPOSITE_FOREGROUND, COMPOSITE_ALPHA, COMPOSITE_INVERTED_ALPHA, COMPOSITE_LUM, COMPOSITE_INVERTED_LUM = range(32)

class OCAImport():
    filename = ""
    # https://pedrolabonia.github.io/pydavinci/project/
    project = None
    # https://pedrolabonia.github.io/pydavinci/mediapool/
    mediapool = None
    timeline = None
    poolfolder = None
    # compoundfolder = None
    duplicateStills = True
    importMethod = 0
    compoundClips = []
    
    def __init__(self):
        self.filename = ""
        
    def load(self, f = None):
        self.filename = f
        title = os.path.basename(self.filename)
        self.project = projectManager.GetCurrentProject()
        if not self.project:
            self.project = projectManager.CreateProject(title)
        if not self.project:
            print("OCAImport: Unable to create project '" + title)
            return
        self.mediapool = self.project.GetMediaPool()
        if not self.mediapool:
            print("OCAImport: Unable get mediapool")
            return
        timelineName = title + "_" + str(self.project.GetTimelineCount())
        self.timeline = self.mediapool.CreateEmptyTimeline( timelineName )
        if not self.timeline:
            print("OCAImport: Unable to create timeline '" + timelineName + "'")
            return
        if not self.timeline.SetStartTimecode("00:00:00:01"):
            print("OCAImport: Unable to set start TC for timeline '" + timelineName + "'")
            return
        self.project.SetCurrentTimeline(self.timeline)
        with open(self.filename, "r") as read_file:
            oca = json.load(read_file)
            self.project.SetSetting("timelineFrameRate", oca["frameRate"])
            self.project.SetSetting("timelineResolutionWidth", oca["width"])
            self.project.SetSetting("timelineResolutionHeight", oca["height"])
            resolve.OpenPage('edit')
            rootFolder = self.mediapool.GetRootFolder()
            self.poolfolder = self.mediapool.AddSubFolder(rootFolder, timelineName)
            self.mediapool.SetCurrentFolder(self.poolfolder)
            self.importLayers(oca, os.path.dirname(self.filename))
            if self.importMethod >= 1 :
                compoundfolder = self.mediapool.AddSubFolder(self.poolfolder, "compounds")
                self.mediapool.SetCurrentFolder(compoundfolder)
                # MoveClips fails !?
                # MoveClips([clips], targetFolder)                --> Bool               # Moves specified clips to target folder.
                if not self.mediapool.MoveClips(self.compoundClips , compoundfolder) :# strange : MoveClips auto sets current folder ?
                    print("OCAImport: Unable to MoveClips in 'compounds' Bin.")
                # precomp
                # CreateFusionClip([timelineItems])               --> timelineItem       
                # Creates a Fusion clip of input timeline items. It returns the created timeline item
                if self.importMethod >= 3 :
                    self.fusionPrecomp(oca)
                        
    def fusionPrecomp(self, oca):
        fusionfolder = self.mediapool.AddSubFolder(self.poolfolder, "fusion")
        self.mediapool.SetCurrentFolder(fusionfolder)
        fusionClip = self.timeline.CreateFusionClip(self.compoundClips)
        # set clip name not possible on existing clips : https://forum.blackmagicdesign.com/viewtopic.php?t=156136&p=989212
        # print ("fusionClip name: " + fusionClip.GetProperty("Name"))
        # fusionClip.SetName("")
        # fusionClip.SetProperty("Name", timelineName + "_comp")
        self.mediapool.AppendToTimeline( [fusionClip] )
        # retrieve the fusion comp..
        resolve.OpenPage("fusion")
        # comp = self.timeline.GetFusionCompByIndex(self.timeline.GetFusionCompCount())
        composition = fusion.GetCurrentComp()
        if composition:
            # https://documents.blackmagicdesign.com/UserManuals/Fusion8_Scripting_Guide.pdf
            # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=4317
            # pprint(fusionComp)
            composition.SetPrefs(
                    {
                        "Comp.FrameFormat.Width"    :   oca["width"],
                        "Comp.FrameFormat.Height"   :   oca["height"],
                        "Comp.FrameFormat.Rate"     :   oca["frameRate"],
                        "Comp.Unsorted.GlobalStart" :   oca["startTime"],
                        "Comp.Unsorted.GlobalEnd"   :   oca["endTime"]
                    }
                )
            composition.SetAttrs(
                    {
                        "COMPN_GlobalStart" : oca["startTime"],
                        "COMPN_RenderStart" : oca["startTime"],
                        "COMPN_GlobalEnd" : oca["endTime"],
                        "COMPN_RenderEnd" : oca["endTime"]
                    }
                )
            # firstMerge = comp.FindTool("Merge")
            merges = composition.GetToolList(False, "Merge")
            pprint(merges)
            # Not easy to change FuID parameters...
            # How to change merge's ApplyMode parameter ???
            # hum https://forum.blackmagicdesign.com/viewtopic.php?f=22&t=173516
            # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=1128
            # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=2012
            # or type in lua console: dump(fusion:GetHelp('Fusion'))
            # see https://github.com/Colorbleed/fusionless/blob/4ff726c64e40f48383ddb032267587722712aaff/fusionless/core.py#L1348
            # see P:\workflow\dev\janimatic\fusion\Scripts\Comp\HoS\PSDLayers.lua !
            for k, v in merges.items():
                """
                pprint(v.ApplyMode)
                # v.SetAttrs({"ApplyMode" : "Multiply"})
                fuIdInputParam = v.ApplyMode
                attrs = fuIdInputParam.GetAttrs()
                data_type = attrs['INPS_DataType']
                if data_type == "FuID":
                    enum = attrs["INPIDT_ComboControl_ID"]
                """
                # When importing T2D drawings, there is no alpha because it uses RGBM (it treats white as transparent)
                # Thus mult would de better, except for BG, in that case...
                if k > 1 and oca["originApp"] == "Tahoma2D":
                    # v.ApplyMode = self.convertBlendingModeKritaToFusion("multiply")
                    composition.Execute(v.Name + '.ApplyMode = "Multiply"')
                else:
                    layer = oca["layers"][k - 1]
                    # v.ApplyMode = self.convertBlendingModeKritaToFusion(layer["blendingMode"])
                    composition.Execute(v.Name + '.ApplyMode = "Multiply"')
    
    def importLayers(self, oca, parentDir):
        for layer in oca["layers"]:
            if layer["type"] == "paintlayer":
                print("OCAImport: create layer " + layer["name"])
                # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=4754
                # https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=113040 << Undocumented Resolve API functions!!
                trackIndex = int(self.timeline.GetTrackCount("video"))
                if not self.timeline.AddTrack('video') :
                    print("OCAImport: Unable to add track " + layer["name"])
                    return;
                else :
                    print("OCAImport: add track " + str(trackIndex) + " " + layer["name"])
                self.timeline.SetTrackName('video', trackIndex, layer["name"]) 
                # newLayer = timeline.createTrack(layer["name"], "paintLayer")
                for frame in layer["frames"]:
                    # just skip blank frames
                    if frame["fileName"] == "" or frame["name"] == "_blank" :
                        continue
                    # AppendToTimeline([{clipInfo}, ...])             --> [TimelineItem]     
                    # Appends list of clipInfos specified as dict of "mediaPoolItem", "startFrame" (int), "endFrame" (int), (optional) "mediaType" (int; 1 - Video only, 2 - Audio only), "trackIndex" (int) and "recordFrame" (int). Returns the list of appended timelineItems.
                    # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=5698
                    # https://github.com/ntbone/DaVinci-Resolve-Shared-Scripts/blob/main/update_clip_camera_angles_and_timecode_from_timeline.py
                    # https://forum.blackmagicdesign.com/viewtopic.php?f=12&t=190945&p=998174&hilit=AppendToTimeline#p998174
                    # https://forum.blackmagicdesign.com/viewtopic.php?t=115919&p=666318
                    print("OCAImport:  create frame " + str(frame["frameNumber"]) + " : " + frame["fileName"])
                    frames = [ parentDir + "/" + frame["fileName"] ]
                    media = self.mediapool.ImportMedia(frames)
                    if len(media) < 1 :
                        print("OCAImport:  Unable to ImportMedia " + str(frame["frameNumber"]) + " : " + frame["fileName"])
                        continue
                    if media[0].GetClipProperty()["Video Codec"] == "":
                        print("OCAImport:  skipping frame with no video codec    " + str(frame["frameNumber"]) + " : " + frame["fileName"])
                        continue
                        
                    # a single call to AppendToTimeline reduces slowness a little bit...
                    subClips = []
                    for rf in range(frame["duration"]) :
                        subClip = {
                            "mediaPoolItem": media[0],
                            "startFrame": 0,
                            "endFrame": 1,
                            "recordFrame": frame["frameNumber"] + rf,
                            "trackIndex": trackIndex,
                            "mediaType": 1,
                        }
                        subClips.append(subClip)
                    items = self.mediapool.AppendToTimeline( subClips )
                    # if self.importMethod >= 1 and len(items) > 1 :
                    if self.importMethod >= 1 :
                        # CreateCompoundClip([timelineItems], {clipInfo}) --> timelineItem       
                        # Creates a compound clip of input timeline items with an optional clipInfo map: 
                        # {"startTimecode" : "00:00:00:00", "name" : "Compound Clip 1"}. It returns the created timeline item. 
                        compound = self.timeline.CreateCompoundClip(items, {"startTimecode" : "00:00:00:00", "name" : frame["name"]})
                        # CreateFusionClip
                        
                        if self.importMethod >= 2 :
                            # precomp in Edit page
                            if trackIndex > 1 and oca["originApp"] == "Tahoma2D":
                                # When importing T2D drawings, there is no alpha because it uses RGBM (it treats white as transparent)
                                # Thus mutli would de better, except for BG
                                compound.SetProperty("CompositeMode", COMPOSITE_MULTIPLY)
                            else :
                                compound.SetProperty("CompositeMode", self.convertBlendingModeKritaToResolve(layer["blendingMode"]) )
                        self.compoundClips.append(compound)
                            
    def getTimelineByName(self, name):
        if not self.project:
            return None
        for index in range(1, int(self.project.GetTimelineCount()) + 1) :
            if self.project.GetTimelineByIndex(index).name == name :
                return self.project.GetTimelineByIndex(index)
        return None

    def timelineExists(self, name):
        if not self.project:
            return False
        for index in range (1, int(self.project.GetTimelineCount()) + 1):
            if self.project.GetTimelineByIndex(index).name == name :
                return True
        return False
        
    def setImportMethod(self, m):
        self.importMethod = m
        
    def convertBlendingModeKritaToResolve(self, modeString):
        # http://oca.rxlab.guide/specs/blending-modes.html
        # missing COMPOSITE_INVERTED_LUM ? COMPOSITE_FOREGROUND ?
        if modeString == "normal":
            return COMPOSITE_NORMAL
        elif modeString == "add":
            return COMPOSITE_ADD
        elif modeString == "subtract":
            return COMPOSITE_SUBTRACT
        elif modeString == "difference":
            return COMPOSITE_DIFF
        elif modeString == "multiply":
            return COMPOSITE_MULTIPLY
        elif modeString == "screen":
            return COMPOSITE_SCREEN
        elif modeString == "overlay":
            return COMPOSITE_OVERLAY
        elif modeString == "heat_glow":
            return COMPOSITE_HARDLIGHT
        elif modeString == "soft_light":
            return COMPOSITE_SOFTLIGHT
        elif modeString == "darken":
            return COMPOSITE_DARKEN
        elif modeString == "lighten":
            return COMPOSITE_LIGHTEN
        elif modeString == "dodge":
            return COMPOSITE_COLOR_DODGE
        elif modeString == "burn":
            return COMPOSITE_COLOR_BURN
        elif modeString == "exclusion":
            return COMPOSITE_EXCLUSION
        elif modeString == "hue":
            return COMPOSITE_HUE
        elif modeString == "saturation":
            return COMPOSITE_SATURATE
        elif modeString == "color":
            return COMPOSITE_COLORIZE
        elif modeString == "divide":
            return COMPOSITE_DIVIDE
        elif modeString == "linear_dodge":
            return COMPOSITE_LINEAR_DODGE
        elif modeString == "inverse_subtract":
            return COMPOSITE_LINEAR_BURN
        elif modeString == "linear_light":
            return COMPOSITE_LINEAR_LIGHT
        elif modeString == "flat_light":
            return COMPOSITE_VIVID_LIGHT
        elif modeString == "pin_light":
            return COMPOSITE_PIN_LIGHT
        elif modeString == "hard_mix":
            return COMPOSITE_HARD_MIX
        elif modeString == "lighter_color":
            return COMPOSITE_LIGHTER_COLOR
        elif modeString == "darker_color":
            return COMPOSITE_DARKER_COLOR
        elif modeString == "intensity":
            return COMPOSITE_LUM
        # the following remains to validate...
        elif modeString == "stencil_alpha":
            return COMPOSITE_ALPHA  # not sure!
        elif modeString == "erase":
            return COMPOSITE_INVERTED_ALPHA # not sure!
        elif modeString == "alpha_darken": 
            return COMPOSITE_LUMA_MASK # not sure!
        return COMPOSITE_NORMAL

    def convertBlendingModeKritaToFusion(self, modeString):
        # missing : Hypotenus? Geometric ?
        if modeString == "burn":
            return "Color Burn"
        elif modeString == "inverse_subtract":
            return "Linear Burn"
        elif modeString == "dodge":
            return "Color Dodge"
        elif modeString == "heat_glow":
            return "Hard Light"
        elif modeString == "flat_light":
            return "Vivid Light"
        modeString = modeString.replace("_", " ")
        return capitalize(modeString)

###########################################################################################################################
# UI
###########################################################################################################################

ui = fu.UIManager
dispatcher = bmd.UIDispatcher(ui)
ocai = OCAImport()
# win = dispatcher.AddWindow({ 'ID': 'myWindow' }, [ ui.Label({ 'Text': 'Hello World!' }) ])
win = dispatcher.AddWindow({'WindowTitle': 'OCA import', 'ID': 'myWindow', 'Geometry': [100, 100, 500, 100],},[
    ui.VGroup({'Spacing': 0,},[
        # Add your GUI elements here:
        ui.HGroup({'Weight': 0.1},[
            ui.ComboBox({"ID": "ImportCombo", "Text": "Combo Menu"}),
        ]),
        ui.VGap(),
        ui.HGroup({'Weight': 0.0,},[
            ui.Label({'ID': 'Label', 'Text': 'Filename', 'Weight': 0.1}),
            ui.LineEdit({'ID': 'FileLineTxt', 'Text': '', 'PlaceholderText': 'Please Enter a filepath', 'Weight': 0.9}),
            ui.Button({'ID': 'BrowseButton', 'Text': 'Browse', 'Geometry': [0, 0, 30, 50], 'Weight': 0.1}),
        ]),
        ui.VGap(),
        ui.HGroup({'Weight': 0.1},[
            ui.Button({'ID': 'OpenButton', 'Text': 'Load OCA file', 'Geometry': [0, 0, 30, 50], 'Weight': 0.1}),
        ]),
    ]),
])

items = win.GetItems()
items['ImportCombo'].AddItem("Import in Edit (duplicate / stills)")
items['ImportCombo'].AddItem("Import in Edit (compound clip / stills)")
items['ImportCombo'].AddItem("Precomp in Edit")
items['ImportCombo'].AddItem("Precomp in Fusion")

def OnImportComboChanged(ev):
    ocai.setImportMethod(items['ImportCombo'].CurrentIndex)
win.On.ImportCombo.CurrentIndexChanged = OnImportComboChanged
items['ImportCombo'].CurrentIndex = 3

def OnClose(ev):
    dispatcher.ExitLoop()
win.On.myWindow.Close = OnClose 

def onBrowse(ev):
    # selectedPath = fu.RequestFile()
    # https://www.steakunderwater.com/wesuckless/viewtopic.php?t=4130
    parentFolder = r'P:\Projets'
    # selectedPath = fu.RequestFile(parentFolder, "", {FReqS_Filter = "Open Cell Animation (*.oca)|*.oca"})
    # selectedPath = fu.RequestFile(parentFolder, "toto", {FReqS_Filter = "Open Cell Animation (*.oca)|*.oca"})
    # https://github.com/nakano000/Resolve_Script/blob/81663201821a737dc507819bc37721455cafa0de/Scripts/Comp/Prototype/Import(PsdSplitter)_NO_EXP.py3#L7
    selectedPath = fu.RequestFile(
        '',  # dir
        '',  # file
        {
            'FReqB_SeqGather': False,
            'FReqS_Filter': 'Open Cell Animation (*.oca)|*.oca',
            'FReqS_Title': 'Choose *.oca file',
        },
    )
    if selectedPath:
        items['FileLineTxt'].Text = str(selectedPath)
        # ocai.load(str(selectedPath))
        # win.Hide()
win.On.BrowseButton.Clicked = onBrowse

def onOpen(ev):
    # print('[Open File] Button Clicked')
    if items['FileLineTxt'].Text != "":
        ocai.load(items['FileLineTxt'].Text)
        dispatcher.ExitLoop()
win.On.OpenButton.Clicked = onOpen

win.Show()
dispatcher.RunLoop()
win.Hide()
