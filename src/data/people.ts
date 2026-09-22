import { parse } from 'yaml';
import peopleRaw from './people.yaml?raw';

export type PersonGroup =
  | 'director'
  | 'postdoc'
  | 'phd'
  | 'assistant'
  | 'manager'
  | 'affiliate'
  | 'visitor'
  | 'alumni';

export interface Person {
  slug: string;
  name: string;
  role: string;
  group: PersonGroup;
  url?: string;
  email?: string;
  photo?: string;
  bio?: string;
  scholar?: string;
}

const loaded = parse(peopleRaw) as { people: Person[] };

export const PEOPLE: Person[] = loaded.people;

const byGroup = (group: PersonGroup) => PEOPLE.filter(p => p.group === group);

export const DIRECTOR = byGroup('director');
export const POSTDOCS = byGroup('postdoc');
export const PHD_STUDENTS = byGroup('phd');
export const ASSISTANTS = byGroup('assistant');
export const LAB_MANAGERS = byGroup('manager');
export const AFFILIATES = byGroup('affiliate');
export const VISITORS = byGroup('visitor');
export const ALUMNI = byGroup('alumni');

export const GROUP_LABELS: Record<PersonGroup, string> = {
  director: 'Director',
  postdoc: 'Postdoctoral Researcher',
  phd: 'PhD Student',
  assistant: 'Scientific Assistant',
  manager: 'Lab Manager',
  affiliate: 'Faculty Affiliate',
  visitor: 'Visiting Student',
  alumni: 'Former group member',
};

export function personBySlug(slug: string): Person | undefined {
  return PEOPLE.find(p => p.slug === slug);
}
