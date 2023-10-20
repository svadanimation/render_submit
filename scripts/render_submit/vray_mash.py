import maya.cmds as mc # pylint: disable=import-error
import os

def instancerPreExport():
    print ('instancer pre export')
    #find the start frame
    startFrame = int(mc.getAttr("defaultRenderGlobals.startFrame"))
    
    #find and filter all the instancers
    mashInstancers = []

    instancers = mc.ls(type='instancer')
    if instancers:
        for i in instancers:
            if mc.attributeQuery( 'instancerMessage', node=i, exists=True ):
                connection = mc.listConnections(i + '.instancerMessage')
                if connection is not None:
                    if mc.objectType(connection[0], isType='MASH_Waiter'):
                        if mc.getAttr(i +'.visibility') == 1:
                            if mc.attributeQuery( 'override', node=i, exists=True ):
                                if mc.getAttr(i + '.override'):
                                    mashInstancers.append(i)
                                    print ('added' + i)
                                    
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
        if mashInstancers:
            
            #set a key on the instancers on first visible frame
            mashAnimCurve = mc.createNode('animCurveTU', name='MASH_instancer_visibility')
            mc.setKeyframe(mashAnimCurve, time=(startFrame), v=1, itt='stepnext', ott='step')
            mc.setKeyframe(mashAnimCurve, time=(startFrame+1), v=0,  itt='stepnext', ott='step')
            
            for mi in mashInstancers:
                mc.connectAttr(mashAnimCurve + '.output', mi + '.visibility', force=True)
            print ('Instancers:')
            print (mashInstancers)
            return mashInstancers
    else:
        mc.warning('No instancers found')
        return None


def instancerPostExport(mashInstancers, vrscene):
    print ('instancer post export')
    #Find the path to the .vrscene

    uniquePath = vrscene
    if os.path.isfile(uniquePath):
        expand = 1
        while True:
            expand += 1
            new_file_name = uniquePath.split(".vrscene")[0] + '_' + str(expand) + ".vrscene"
            if os.path.isfile(new_file_name):
                continue
            else:
                print ('Existing cache file, incrementing to ' + new_file_name)
                #unfortunately, we can't simply replace the file since it has an open handle
                #os.rename(uniquePath, new_file_name)
                uniquePath = os.path.normpath(new_file_name)
                print (uniquePath)
                break
    
    
    os.rename(vrscene, uniquePath)
    sourceFile = uniquePath
    destFile= vrscene
    
    print ('processing')
    print (mashInstancers)
    #vray uses a __ instead of a : for namespaces
    mashInstancersNS = [m.replace(':','__') for m in mashInstancers]
    print ('adjust ns')
    print (mashInstancersNS)
    start = mc.timerX()
    
    
    foundInstancerData = {}
    for mi in mashInstancersNS:
        foundInstancerData[mi] = 0   
    
    with open(sourceFile, 'r') as source:
        with open(destFile, 'w') as dest:        
            shouldWrite = True
            inBlock = False
            currentInstancer = ''
            for line in source:
                #print writeLine
                #print 'block' + str(inBlock)
                #print instancerData
                 
                if line.startswith('Instancer'):
                    #check against eash flagged instancer
                    for mi in mashInstancersNS:
                        if mi in line:
                            inBlock = True
                            #print mi
                            currentInstancer = mi
                            if foundInstancerData[currentInstancer] > 0:
                                #print line
                                shouldWrite = False
                            break                                           
                
                #would be nice to figure out how to quit checking for data once we've found it all
                elif line.lstrip().startswith('instances') and inBlock:
                    foundInstancerData[currentInstancer] = foundInstancerData[currentInstancer]+1
                    #print 'found data ' + currentInstancer 
                    
                #if we hit the } we are done with the block                                   
                elif line.startswith('}') and inBlock:
                    shouldWrite = True
                    inBlock = False
                    if foundInstancerData[currentInstancer] > 1:
                        continue
                                
                    
                if shouldWrite:
                    dest.write(line)        
                   
    source.close()
    dest.close()
    
    print ('end processing')
    totalTime = mc.timerX(startTime=start)
    print (totalTime)
    
    instancerPostReset(mashInstancers)        
        
        
def instancerPostReset(mashInstancers):
    #reset all instancers visibility
    if mashInstancers:
        for mi in mashInstancers:
            animCurve = mc.listConnections(mi + '.visibility')
            if animCurve is not None:
                mc.delete(animCurve)
            mc.setAttr(mi + '.visibility', 1)
