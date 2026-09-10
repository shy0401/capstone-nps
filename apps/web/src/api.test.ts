import {describe,it,expect} from 'vitest';
import {canGenerate,stateLabel} from './api';
describe('review gate presentation',()=>{
 it('blocks drafts and stale approval',()=>{expect(canGenerate('DRAFT',1,null)).toBe(false);expect(canGenerate('APPROVED',2,1)).toBe(false);});
 it('allows current approval',()=>expect(canGenerate('APPROVED',2,2)).toBe(true));
 it('allows explicit prototype pass without inventing approval',()=>expect(canGenerate('DRAFT',2,null,true)).toBe(true));
 it('provides textual failure and cancel states',()=>{expect(stateLabel.FAILED).toBe('실패');expect(stateLabel.CANCELLED).toBe('취소됨');});
});
