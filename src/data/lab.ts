import { parse } from 'yaml';
import labRaw from './lab.yaml?raw';

export interface LabLink {
  text: string;
  url: string;
}

export interface LabTheme {
  title: string;
  blurb: string;
}

export interface Lab {
  name: string;
  short_name: string;
  tagline: string;
  location: string;
  email: string;
  mission: string;
  themes: LabTheme[];
  affiliations: LabLink[];
  links: LabLink[];
}

export const LAB: Lab = parse(labRaw) as Lab;
