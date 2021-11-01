Name:    ices0
Version: 0.4
Release: 4%{?dist}
Summary: Source streaming for Icecast
Group:   System Environment/Daemons
License: GPLv2
URL:     http://www.icecast.org
Source0: http://downloads.us.xiph.org/releases/ices/ices-0.4.tar.gz
Source1: ices.init
Source2: ices.logrotate
Patch0:  ices.conf.patch
Patch1:  ices.exit0.patch
Patch2:  ices0.die-dreaded-daemon-message.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: gcc-c++
BuildRequires: libxml2-devel, libshout-devel >= 2.0, libvorbis-devel,
BuildRequires: alsa-lib-devel, pkgconfig, zlib-devel, lame-devel, libogg-devel
Requires(post): /sbin/chkconfig
Requires(post): /sbin/service
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service

%description
IceS is a source client for a streaming server. The purpose of this client is
to provide an audio stream to a streaming server such that one or more
listeners can access the stream. With this layout, this source client can be
situated remotely from the icecast server.

The primary example of a streaming server used is Icecast 2, although others
could be used if certain conditions are met. 
The main advantage of ices0 is that it is able to broadcast in mp3 format.

%prep
%setup -q -n ices-%{version}
%patch0 -p0 -b .ices.conf
%patch1 -p0 -b .ices.exit0
%patch2 -p1 -b .ices0.die-dreaded-daemon-message
# Avoid standard rpaths on lib64 archs:
sed -i -e 's|"/lib /usr/lib\b|"/%{_lib} %{_libdir}|' configure
perl -pi -e 's/\#include \<parser.h\>/\#include \<libxml\/parser.h\>/' src/ices_config.c
perl -pi -e 's/\#include \<xmlmemory.h\>/\#include \<libxml\/xmlmemory.h\>/' src/ices_config.c
iconv -f iso8859-1 -t utf8 README -o README.txt
touch -r README README.txt
mv README.txt README

perl -pi -e 's!<BaseDirectory>.*</BaseDirectory>!<BaseDirectory>%_var/log/%name</BaseDirectory>!' conf/ices.conf.dist.in

%build
%configure --without-faad --without-flac --with-lame --with-vorbis

%{__make} %{?_smp_mflags}

%install
rm -rf %{buildroot}

install -D -m 755 src/ices %{buildroot}%{_bindir}/%{name}
install -D -m 644 conf/ices.conf.dist %{buildroot}%{_sysconfdir}/%{name}.conf
install -D -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}
install -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -d -m 755 %{buildroot}%{_var}/log/%{name}

%clean 
rm -rf %{buildroot}

%pre
# add user ices0
/usr/sbin/useradd -c "IceS Shoutcast source" \
    -s /sbin/nologin -r -d / %{name} 2> /dev/null || :

%post
# installing rpm - add service
if [ "$1" -eq "1" ]; then
     /sbin/chkconfig --add %{name}
fi
/sbin/service %{name} condrestart &>/dev/null || :

%preun
# removing rpm - stop and remove service 
if [ "$1" -eq "0" ]; then
     /sbin/service %{name} stop >/dev/null 2>&1
     /sbin/chkconfig --del %{name}
fi

%postun
if [ "$1" -ge "1" ]; then
     /sbin/service %{name} condrestart &>/dev/null || :
fi

%files
%defattr(-,root,root)
%doc AUTHORS COPYING README TODO doc/*.html conf/ices.p* conf/ices.conf.dist
%{_bindir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config %{_sysconfdir}/logrotate.d/%{name}
%{_initrddir}/%{name}
%attr(0770,root,%{name}) %{_var}/log/%{name}

%changelog
* Sat Jun 13 2009 Paulo Roma <roma@lcg.ufrj.br> - 0.4-4
- Fixed ices0.init (stat).
- Not starting service ices0 by default.
- Converted README to utf8.
- Removed rpath from binary.

* Thu Jan 11 2007 Paulo Roma <roma@lcg.ufrj.br> - 0.4-3
- Fixed ices0 user initial directory.
- Added dreaded daemon message patch.

* Thu Jan 11 2007 Paulo Roma <roma@lcg.ufrj.br> - 0.4-2
- Switched to ices0 for mp3 support.

* Fri Sep 08 2006 Andreas Thienemann <andreas@bawue.net> - 2.0.1-3
- FE6 Rebuild

* Tue Mar 28 2006 Andreas Thienemann <andreas@bawue.net> 2.0.1-2
- Cleaned up the specfile for FE

* Thu Nov 17 2005 Matt Domsch <Matt_Domsch@dell.com> 2.0.1-1
- add dist tag
- rebuild for FC4

* Mon Jan 31 2005 Ignacio Vazquez-Abrams <ivazquez@ivazquez.net> 0:2.0.1-0.iva.0
- Upstream update

* Fri Jan  7 2005 Ignacio Vazquez-Abrams <ivazquez@ivazquez.net> 0:2.0.0-0.iva.0
- Retooled for Fedora Core 3
