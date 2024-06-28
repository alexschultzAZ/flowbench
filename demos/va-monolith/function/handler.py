from .vidsplit import vidsplit_metrics
# from .modect import modect_handler
# from .facextract import facextract_handler
# from .facerec import facerec_handler
def handle(req):
    output1 = vidsplit_metrics.vidsplit_handler(req)
    # output2 = modect_handler.modect_handler(output1)
    # output3 = facextract_handler.facextract_handler(output2)
    # output4 = facerec_handler.facerec_handler(output3)
    return output1