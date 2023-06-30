## {{ versiondata.version }} ({{ versiondata.date }})
{%- for section, _ in sections.items() -%}
  {%- if section -%}
### {{ section }}{%- endif -%}
  {%- if sections[section] -%}
    {%- for category, val in definitions.items() if category in sections[section] %}


### {{ definitions[category]['name'] }}

      {%- if definitions[category]['showcontent'] %}
        {%- for text, values in sections[section][category].items() %}
          {%- if values[0].endswith("/0)") %}

* {{ definitions[category]['name'] }} without explicit PR/issue numbers
  {{ text }}
          {%- else %}

* {{ text }} {{ values|join(',\n  ') }}
          {%- endif %}

        {%- endfor %}
      {%- else %}

* {{ sections[section][category]['']|join(', ') }}
      {%- endif %}
      {%- if sections[section][category]|length == 0 %}

No significant changes.
      {%- else %}
      {%- endif %}

    {%- endfor %}
    {%- else %}

No significant changes.
  {%- endif %}
{%- endfor %}
