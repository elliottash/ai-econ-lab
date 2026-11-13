import { parse } from 'yaml';
import grantsRaw from './grants.yaml?raw';
import type { Stat } from './papers';

export interface GrantLink {
  text: string;
  url: string;
}

export interface Grant {
  acronym?: string;
  title: string;
  scheme: string;
  amount?: string;
  period?: string;
  role?: string;
  lead?: string;
  host?: string;
  partners?: string;
  featured?: boolean;
  summary?: string;
  links?: GrantLink[];
  stats?: Stat[];
}

export interface GrantsData {
  grants: Grant[];
  other_funding: string[];
}

const data = parse(grantsRaw) as GrantsData;

export const GRANTS: Grant[] = data.grants;
export const OTHER_FUNDING: string[] = data.other_funding;
