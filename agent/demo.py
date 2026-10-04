"""Generate clearly fictional events for offline previews and UI testing."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate(output: Path):
    now = datetime.now(timezone(timedelta(hours=5)))
    samples = [
        (2, 'Build your first AI agent', 'Example · Karachi Builders', 'A hands-on afternoon turning an idea into an agent. Bring your laptop and your curiosity.', ['Agents', 'AI/ML'], 'in-person', 'Karachi · sample venue', True, False, 'Luma'),
        (3, 'Machine learning, from the ground up', 'Example · Campus Tech Society', 'A beginner-friendly workshop on models, datasets and getting your first experiment running.', ['AI/ML', 'Students'], 'in-person', 'University campus · Karachi', True, True, 'University society'),
        (5, 'Climate tech: ideas into action', 'Example · Green City Collective', 'Meet people working on cleaner cities, circular systems and practical climate solutions.', ['Sustainability', 'Emerging Tech'], 'in-person', 'Karachi · sample venue', True, False, 'Eventbrite'),
        (6, 'Beyond the chatbot: agent workflows', 'Example · Open Builders', 'An online session exploring tools, memory and the decisions behind useful AI workflows.', ['Agents', 'AI/ML'], 'online', 'Online', True, False, 'Meetup'),
        (9, 'The next wave of emerging technology', 'Example · Developer Community', 'An evening of short talks on what developers are experimenting with next.', ['Emerging Tech'], 'in-person', 'Karachi · sample venue', False, False, 'GDG'),
        (12, 'Student makers: prototype weekend', 'Example · Makers Society', 'Find a team, test an idea and share a working prototype with other student builders.', ['Students', 'Emerging Tech'], 'in-person', 'University campus · Karachi', True, True, 'University society'),
        (16, 'Designing a more sustainable web', 'Example · Digital Futures', 'Explore the intersection of software, thoughtful design and lower-impact digital products.', ['Sustainability'], 'online', 'Online', True, False, 'Luma'),
        (22, 'Practical ML: a project clinic', 'Example · Data Circle', 'Bring an experiment and work through evaluation, data quality and deployment questions.', ['AI/ML'], 'online', 'Online', False, False, 'Meetup'),
    ]
    events = []
    for i, (days, title, organizer, description, categories, fmt, venue, free, student, source) in enumerate(samples):
        start = (now + timedelta(days=days)).replace(hour=17 if i % 2 == 0 else 14, minute=0, second=0, microsecond=0)
        events.append(dict(id=f'demo-{i}',title=title,organizer=organizer,description=description,categories=categories,format=fmt,venue=venue,is_free=free,cost='Free' if free else 'PKR 1,500 · sample',student_only=student,start=start.isoformat(),end=(start+timedelta(hours=3)).isoformat(),time_known=True,source_name=source,source_url='',registration_url='',verification='unverified',verification_reason='Fictional sample event.',confidence=0,first_seen=(now-timedelta(days=1 if i < 4 else 9)).isoformat(),last_checked=now.isoformat()))
    output.mkdir(parents=True, exist_ok=True)
    (output/'events.json').write_text(json.dumps(dict(schema_version=1,mode='demo',generated_at=now.isoformat(),events=events),indent=2)+'\n',encoding='utf-8')
    (output/'status.json').write_text(json.dumps(dict(state='demo',last_attempt=now.isoformat(),last_success=None,message='Fictional preview. Run the agent with API keys to collect real events.'),indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('.artifacts/demo'))
    args = parser.parse_args()
    generate(args.output)
