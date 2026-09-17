import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import cog_core as core

class DesignTests(unittest.TestCase):
    def setUp(self):
        self.input=json.loads((ROOT/'examples/sample-bundle.json').read_text())
        self.output=json.loads((ROOT/'context/output-example.json').read_text())
    def test_example(self):
        self.assertEqual(core.validate_input(self.input),[]);self.assertEqual(core.validate_output(self.output,self.input),[])
    def test_graph_failures(self):
        for edit in (lambda p:p['steps'].reverse(),lambda p:p['steps'][0]['inputs'].append('absent'),lambda p:p['steps'][0]['outputs'].append('notes'),lambda p:p['outputs'].append('missing'),lambda p:p['steps'][0]['criteria'].append('missing')):
            value=copy.deepcopy(self.output);edit(value);self.assertTrue(core.validate_output(value,self.input))
    def test_grounded_catalog_reuse(self):
        card={'id':'example/extractor','version':'1','summary':'extract','accepts':['notes'],'produces':['action-extraction'],'capabilities':[],'fingerprint':'a'*64}
        self.input['catalog']=[card]
        self.output['steps'][0]['choice']={'kind':'existing','cog_id':card['id'],'catalog_fingerprint':card['fingerprint'],'brief_id':None,'rationale':'Declared output matches.'};self.output['cog_briefs']=[]
        self.assertEqual(core.validate_output(self.output,self.input),[])
        self.output['steps'][0]['choice']['catalog_fingerprint']='b'*64
        self.assertTrue(core.validate_output(self.output,self.input))
    def test_invented_existing_cog(self):
        self.output['steps'][0]['choice'].update(kind='existing',cog_id='imaginary/cog',brief_id=None,catalog_fingerprint='a'*64);self.output['cog_briefs']=[]
        self.assertTrue(core.validate_output(self.output,self.input))
    def test_tool_steps(self):
        self.output['steps'][1]['choice']={'kind':'tool','cog_id':None,'catalog_fingerprint':None,'brief_id':None,'rationale':'Write the accepted actions to the tracker.'}
        self.assertEqual(core.validate_output(self.output,self.input),[])
        self.output['steps'][1]['choice']['brief_id']='action-extractor';self.assertTrue(core.validate_output(self.output,self.input))
        self.output['steps'][1]['choice'].update(brief_id=None,rationale=' ');self.assertTrue(core.validate_output(self.output,self.input))
        self.output['steps'][1]['choice'].update(rationale='x',kind='robot');self.assertTrue(core.validate_output(self.output,self.input))
    def test_brief_mapping(self):
        self.output['cog_briefs'][0]['step_ids']=['review'];self.assertTrue(core.validate_output(self.output,self.input))
    def test_criteria_preserved(self):
        self.output['criteria'][0]['description']='Something easier';self.assertTrue(core.validate_output(self.output,self.input))
    def test_remote_schema_rejected(self):
        self.output['artifacts'][0]['schema']={'$ref':'https://example.com/schema'};self.assertTrue(core.validate_output(self.output,self.input))
    def test_nonproposal_cannot_smuggle_steps(self):
        self.output.update(classification='needs_input',questions=['What input?']);self.assertTrue(core.validate_output(self.output,self.input))
    def test_malformed_outputs_do_not_crash(self):
        for k in self.output:
            value=copy.deepcopy(self.output);value[k]=17;self.assertTrue(core.validate_output(value,self.input))
    def test_mock_model_envelope(self):
        body={'model':core.MODEL,'choices':[{'message':{'content':json.dumps(self.output)}}]}
        with patch.object(core,'health',return_value=(True,'mock')),patch.object(core.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            result=core.invoke(self.input)
        self.assertTrue(result['ok']);self.assertEqual(result['problems'],[]);self.assertEqual(result['payload'],self.output)

if __name__=='__main__':unittest.main()
