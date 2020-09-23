# Python Script, API Version = V19

def GetMergedCurves(lines):
    RawCurveSegmentList=List[ITrimmedCurve]()
    for l in lines:
        RawCurveSegmentList.Add(l.Shape)
    FM=SpaceClaim.Api.V19.Geometry.FitMethod.LinesAndSplines
    CurveSegmentGroup=ITrimmedCurve.ApproximateChain(RawCurveSegmentList[0],0.00001,RawCurveSegmentList,FM)
    #print CurveSegmentGroup.Count
    for temp_crv in CurveSegmentGroup:
        DesignCurve.Create(GetRootPart(),temp_crv)
GetMergedCurves(GetActivePart().Curves) #Activate the component and execute the script